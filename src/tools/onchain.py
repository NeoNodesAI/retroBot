"""On-chain inference recording for NeoNodes Agent on Base Mainnet."""
import asyncio
import hashlib
from typing import Optional
from src.utils.logger import logger

CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "prompt", "type": "string"}],
        "name": "requestInference",
        "outputs": [{"internalType": "bytes32", "name": "requestId", "type": "bytes32"}],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "requestId", "type": "bytes32"},
            {"internalType": "string",  "name": "result",    "type": "string"},
            {"internalType": "bytes32", "name": "proofHash", "type": "bytes32"},
        ],
        "name": "submitInference",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "quoteDispatch",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "requestId", "type": "bytes32"},
            {"indexed": True,  "name": "requester", "type": "address"},
            {"indexed": False, "name": "prompt",    "type": "string"},
            {"indexed": False, "name": "fee",       "type": "uint256"},
        ],
        "name": "InferenceRequested",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "requestId", "type": "bytes32"},
            {"indexed": False, "name": "proofHash", "type": "bytes32"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
        ],
        "name": "InferenceFulfilled",
        "type": "event",
    },
]


def _get_web3_and_contract():
    """Return (web3, contract, account) or None if not configured."""
    try:
        from web3 import Web3
        from config.settings import settings

        if not settings.agent_private_key:
            return None

        w3 = Web3(Web3.HTTPProvider(settings.base_rpc_url))
        if not w3.is_connected():
            logger.warning("onchain: Base Mainnet RPC not reachable")
            return None

        account = w3.eth.account.from_key(settings.agent_private_key)
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(settings.agent_contract_address),
            abi=CONTRACT_ABI,
        )
        return w3, contract, account
    except Exception as exc:
        logger.warning(f"onchain: setup failed – {exc}")
        return None


def _build_proof_hash(prompt: str, result: str) -> bytes:
    """Return a 32-byte proof hash from prompt + result."""
    raw = hashlib.sha256(f"{prompt}|{result}".encode()).digest()
    return raw


async def record_inference(prompt: str, result: str, session_id: Optional[str] = None) -> bool:
    """
    Record a completed inference on Base Mainnet.

    Flow:
      1. Call requestInference(prompt) — pays queryFee, returns requestId via event.
      2. Call submitInference(requestId, result, proofHash) — writes proof on-chain.

    Both calls use the agent wallet (AGENT_PRIVATE_KEY in .env).
    Returns True on success, False on any failure (agent response is never blocked).
    """
    setup = _get_web3_and_contract()
    if setup is None:
        return False

    try:
        result_trimmed = result[:500] if len(result) > 500 else result
        return await asyncio.get_event_loop().run_in_executor(
            None, _record_sync, setup, prompt, result_trimmed
        )
    except Exception as exc:
        logger.error(f"onchain: record_inference error – {exc}")
        return False


def _record_sync(setup, prompt: str, result: str) -> bool:
    """Synchronous on-chain recording (runs in thread pool)."""
    from web3 import Web3

    w3, contract, account = setup

    try:
        query_fee: int = contract.functions.quoteDispatch().call()
        nonce     = w3.eth.get_transaction_count(account.address)
        chain_id  = w3.eth.chain_id
        gas_price = w3.eth.gas_price

        # ── Step 1: requestInference ─────────────────────────────────────────
        tx1 = contract.functions.requestInference(prompt).build_transaction({
            "from":     account.address,
            "value":    query_fee,
            "nonce":    nonce,
            "chainId":  chain_id,
            "gas":      200_000,
            "gasPrice": gas_price,
        })
        signed1  = account.sign_transaction(tx1)
        hash1    = w3.eth.send_raw_transaction(signed1.raw_transaction)
        receipt1 = w3.eth.wait_for_transaction_receipt(hash1, timeout=60)

        if receipt1.status != 1:
            logger.error("onchain: requestInference tx failed")
            return False

        # Compute requestId locally — same keccak256 as Solidity contract
        # keccak256(abi.encodePacked(msg.sender, prompt, block.timestamp, requestCount))
        block_data     = w3.eth.get_block(receipt1["blockNumber"])
        block_ts       = block_data["timestamp"]
        count_after    = contract.functions.requestCount().call()
        count_before   = count_after - 1  # requestCount before this tx

        request_id = w3.solidity_keccak(
            ["address", "string", "uint256", "uint256"],
            [account.address, prompt, block_ts, count_before],
        )
        logger.info(f"onchain: requestInference OK – requestId={request_id.hex()[:16]}...")

        # ── Step 2: submitInference ──────────────────────────────────────────
        proof_hash = _build_proof_hash(prompt, result)

        # Estimate gas dynamically, fall back to 500_000
        try:
            estimated_gas = contract.functions.submitInference(
                request_id, result, proof_hash
            ).estimate_gas({"from": account.address})
            gas_limit = int(estimated_gas * 1.3)
        except Exception as est_err:
            logger.warning(f"onchain: gas estimation failed ({est_err}), using 500_000")
            gas_limit = 500_000

        tx2 = contract.functions.submitInference(
            request_id, result, proof_hash
        ).build_transaction({
            "from":     account.address,
            "value":    0,
            "nonce":    nonce + 1,
            "chainId":  chain_id,
            "gas":      gas_limit,
            "gasPrice": gas_price,
        })
        signed2  = account.sign_transaction(tx2)
        hash2    = w3.eth.send_raw_transaction(signed2.raw_transaction)
        receipt2 = w3.eth.wait_for_transaction_receipt(hash2, timeout=60)

        if receipt2.status != 1:
            logger.error(f"onchain: submitInference tx failed – hash={hash2.hex()}")
            return False

        logger.info(
            f"onchain: inference recorded on Base Mainnet – "
            f"txHash={hash2.hex()[:16]}..."
        )
        return True

    except Exception as exc:
        logger.error(f"onchain: _record_sync error – {exc}")
        return False
