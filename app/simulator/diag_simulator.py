"""
Product Diagnostic Simulator

Deterministic rules:

- If the product_version contain '1.6' -> simulate payment gateway timeout
- If the product_version contain 'beta' -> simulate degraded service
- otherwise -> simulate healthy service
"""

from typing import Dict, Any
from datetime import datetime

class ProductDiagSimulator:
    def __init__(self):
        pass

    def run_diagnostic(self, user_id: str, product_version: str) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        pv = (product_version or "").lower()

        if "1.6" in pv:
            return {
                "timestamp": now,
                "payment_gateway_status": "timeout",
                "service_health": "degraded",
                "error_code": ["PAY_GATEWAY_TIMEOUT"],
                "error_message": "Simulated payment gateway timeout for product version 1.6"
            }
        
        if "beta" in pv:
            return {
                "timestamp": now,
                "payment_gateway_status": "slow",
                "service_health": "degraded",
                "error_code": ["SERVICE_HIGH_LATENCY"],
                "error_message": "Simulated degraded performance for beta builds"
            }
        
        return {
            "timestamp": now,
            "payment_gateway_status": "ok",
            "service_health": "healthy",
            "error_code": [],
            "error_message": "All checks passed"
        }