"""Repository for LoginAttempt data access operations."""
from typing import List
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from app.models.login_attempt import LoginAttempt
from app.core.cosmos import cosmos_client


class LoginAttemptRepository:
    """Repository for LoginAttempt entity operations."""
    
    async def create(self, login_attempt: LoginAttempt) -> LoginAttempt:
        """
        Create a new login attempt record.
        
        Args:
            login_attempt: LoginAttempt instance to create
            
        Returns:
            Created LoginAttempt instance
        """
        container = cosmos_client.login_attempts_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")
        
        attempt_dict = login_attempt.model_dump(mode='json')
        container.create_item(body=attempt_dict)
        return login_attempt
    
    async def get_recent_failed_attempts(
        self,
        login_id: str,
        minutes: int = 30
    ) -> List[LoginAttempt]:
        """
        Get recent failed login attempts for a login ID.
        
        Args:
            login_id: User's login identifier
            minutes: Time window in minutes to look back
            
        Returns:
            List of failed LoginAttempt instances
        """
        container = cosmos_client.login_attempts_container
        if not container:
            return []
        
        cutoff_time = datetime.now(UTC) - timedelta(minutes=minutes)
        cutoff_iso = cutoff_time.isoformat()
        
        query = """
            SELECT * FROM c 
            WHERE c.loginId = @loginId 
            AND c.isSuccess = false 
            AND c.attemptedAt >= @cutoffTime
            ORDER BY c.attemptedAt DESC
        """
        parameters = [
            {"name": "@loginId", "value": login_id},
            {"name": "@cutoffTime", "value": cutoff_iso}
        ]
        
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [LoginAttempt(**item) for item in items]
        except Exception:
            return []


# Global repository instance
login_attempt_repository = LoginAttemptRepository()
