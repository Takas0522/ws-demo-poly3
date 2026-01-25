"""Repository for User data access operations."""
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.models.user import User
from app.core.cosmos import cosmos_client


class UserRepository:
    """Repository for User entity operations."""
    
    async def find_by_login_id(self, login_id: str) -> Optional[User]:
        """
        Find a user by login ID.
        
        Args:
            login_id: User's login identifier
            
        Returns:
            User instance or None if not found
        """
        container = cosmos_client.users_container
        if not container:
            return None
        
        query = "SELECT * FROM c WHERE c.loginId = @loginId"
        parameters = [{"name": "@loginId", "value": login_id}]
        
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return User(**items[0])
            return None
        except Exception:
            return None
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User instance or None if not found
        """
        container = cosmos_client.users_container
        if not container:
            return None
        
        try:
            item = container.read_item(item=user_id, partition_key=user_id)
            return User(**item)
        except CosmosResourceNotFoundError:
            return None
        except Exception:
            return None
    
    async def update(self, user: User) -> User:
        """
        Update a user.
        
        Args:
            user: User instance to update
            
        Returns:
            Updated User instance
        """
        container = cosmos_client.users_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")
        
        user_dict = user.model_dump(mode='json')
        container.upsert_item(body=user_dict)
        return user


# Global repository instance
user_repository = UserRepository()
