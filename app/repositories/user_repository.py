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
    
    async def create(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User instance to create
            
        Returns:
            Created User instance
        """
        container = cosmos_client.users_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")
        
        user_dict = user.model_dump(mode='json')
        container.create_item(body=user_dict)
        return user
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        name: Optional[str] = None,
        login_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        List users with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            name: Filter by name (partial match)
            login_id: Filter by login ID (partial match)
            is_active: Filter by active status
            
        Returns:
            Tuple of (list of users, total count)
        """
        container = cosmos_client.users_container
        if not container:
            return [], 0
        
        # Build query with filters
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        parameters = []
        
        if name:
            query_parts.append("AND CONTAINS(LOWER(c.name), @name)")
            parameters.append({"name": "@name", "value": name.lower()})
        
        if login_id:
            query_parts.append("AND CONTAINS(LOWER(c.loginId), @loginId)")
            parameters.append({"name": "@loginId", "value": login_id.lower()})
        
        if is_active is not None:
            query_parts.append("AND c.isActive = @isActive")
            parameters.append({"name": "@isActive", "value": is_active})
        
        # Add sorting
        order = "DESC" if sort_order.lower() == "desc" else "ASC"
        query_parts.append(f"ORDER BY c.{sort_by} {order}")
        
        query = " ".join(query_parts)
        
        try:
            # Get all items (Cosmos DB doesn't support OFFSET/LIMIT in queries)
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            total_count = len(items)
            
            # Apply pagination manually
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_items = items[start_index:end_index]
            
            users = [User(**item) for item in paginated_items]
            return users, total_count
            
        except Exception:
            return [], 0


# Global repository instance
user_repository = UserRepository()
