"""Repository for RefreshToken data access operations."""
from typing import Optional
from datetime import datetime, UTC
from uuid import uuid4
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.models.refresh_token import RefreshToken
from app.core.cosmos import cosmos_client


class RefreshTokenRepository:
    """Repository for RefreshToken entity operations."""
    
    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            refresh_token: RefreshToken instance to create
            
        Returns:
            Created RefreshToken instance
        """
        container = cosmos_client.users_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")
        
        token_dict = refresh_token.model_dump(mode='json')
        container.create_item(body=token_dict)
        return refresh_token
    
    async def find_by_id(self, token_id: str) -> Optional[RefreshToken]:
        """
        Find a refresh token by ID.
        
        Args:
            token_id: Token's unique identifier
            
        Returns:
            RefreshToken instance or None if not found
        """
        container = cosmos_client.users_container
        if not container:
            return None
        
        try:
            item = container.read_item(item=token_id, partition_key=token_id)
            return RefreshToken(**item)
        except CosmosResourceNotFoundError:
            return None
        except Exception:
            return None
    
    async def find_by_user_id(self, user_id: str) -> list[RefreshToken]:
        """
        Find all refresh tokens for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of RefreshToken instances
        """
        container = cosmos_client.users_container
        if not container:
            return []
        
        query = "SELECT * FROM c WHERE c.userId = @userId AND c.isRevoked = false"
        parameters = [{"name": "@userId", "value": user_id}]
        
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [RefreshToken(**item) for item in items]
        except Exception:
            return []
    
    async def update(self, refresh_token: RefreshToken) -> RefreshToken:
        """
        Update a refresh token.
        
        Args:
            refresh_token: RefreshToken instance to update
            
        Returns:
            Updated RefreshToken instance
        """
        container = cosmos_client.users_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")
        
        token_dict = refresh_token.model_dump(mode='json')
        container.upsert_item(body=token_dict)
        return refresh_token
    
    async def revoke(self, token_id: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            token_id: Token's unique identifier
            
        Returns:
            True if token was revoked, False otherwise
        """
        token = await self.find_by_id(token_id)
        if not token:
            return False
        
        token.isRevoked = True
        await self.update(token)
        return True
    
    async def revoke_all_for_user(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Number of tokens revoked
        """
        tokens = await self.find_by_user_id(user_id)
        count = 0
        
        for token in tokens:
            if not token.isRevoked:
                token.isRevoked = True
                await self.update(token)
                count += 1
        
        return count


# Global repository instance
refresh_token_repository = RefreshTokenRepository()
