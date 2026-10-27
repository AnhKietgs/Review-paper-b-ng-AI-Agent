"""Human approval eligibility without silently promoting evidence."""


class ApprovalPolicy:
    """Only supported or explicitly acknowledged uncertain claims may ship."""

    @staticmethod
    def can_approve(
        findings: list[dict], confirmations: set[str] | None = None
    ) -> bool:
        """Keep human-confirmed uncertainty labeled as such."""
        confirmed = confirmations or set()
        return bool(findings) and all(
            item["status"] == "supported"
            or (item["status"] == "needs_human_review" and item["id"] in confirmed)
            for item in findings
        )
