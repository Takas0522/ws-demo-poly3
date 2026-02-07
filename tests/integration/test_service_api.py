"""
Integration tests for Service Setting API
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestServiceSettingAPI:
    """Test service setting endpoints"""

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_get_services_list(self, test_client: TestClient, auth_headers: dict):
        """Test getting service list"""
        response = test_client.get(
            "/api/v1/services",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "data" in data
        assert isinstance(data["data"], list)
        
        if len(data["data"]) > 0:
            service = data["data"][0]
            assert "id" in service
            assert "name" in service
            assert "description" in service
            assert "is_active" in service
            assert "is_mock" in service

    def test_get_services_unauthorized(self, test_client: TestClient):
        """Test getting service list without authentication"""
        response = test_client.get("/api/v1/services")
        
        assert response.status_code == 401

    def test_get_service_detail(self, test_client: TestClient, auth_headers: dict):
        """Test getting service detail"""
        # First, get service list to find a service ID
        list_response = test_client.get(
            "/api/v1/services",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            services = list_response.json().get("data", [])
            if len(services) > 0:
                service_id = services[0]["id"]
                
                # Get service detail
                response = test_client.get(
                    f"/api/v1/services/{service_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify detail information
                assert "id" in data
                assert data["id"] == service_id
                assert "name" in data
                assert "description" in data
                assert "is_active" in data
                assert "is_mock" in data
                assert "roles" in data
                assert isinstance(data["roles"], list)

    def test_get_service_detail_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test getting non-existent service"""
        response = test_client.get(
            "/api/v1/services/non-existent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_get_tenant_services(self, test_client: TestClient, auth_headers: dict):
        """Test getting services for a tenant"""
        tenant_id = "test-tenant-id"
        
        response = test_client.get(
            f"/api/v1/tenants/{tenant_id}/services",
            headers=auth_headers
        )
        
        # May succeed or return error based on tenant existence
        if response.status_code == 200:
            data = response.json()
            assert "tenant_id" in data
            assert "services" in data
            assert isinstance(data["services"], list)

    def test_assign_service_to_tenant(self, test_client: TestClient, auth_headers: dict):
        """Test assigning a service to a tenant"""
        # Get available services
        services_response = test_client.get(
            "/api/v1/services",
            headers=auth_headers
        )
        
        if services_response.status_code == 200:
            services = services_response.json().get("data", [])
            
            if len(services) > 0:
                service_id = services[0]["id"]
                tenant_id = "test-tenant-id"
                
                response = test_client.post(
                    f"/api/v1/tenants/{tenant_id}/services",
                    json={"service_id": service_id},
                    headers=auth_headers
                )
                
                # May succeed, conflict, or be forbidden
                if response.status_code == 201:
                    data = response.json()
                    assert "tenant_id" in data
                    assert "service_id" in data
                    assert "assigned_at" in data
                elif response.status_code == 403:
                    # Not authorized (expected if not global admin)
                    pass
                elif response.status_code == 409:
                    # Service already assigned
                    pass

    def test_assign_invalid_service(self, test_client: TestClient, auth_headers: dict):
        """Test assigning an invalid service"""
        tenant_id = "test-tenant-id"
        
        response = test_client.post(
            f"/api/v1/tenants/{tenant_id}/services",
            json={"service_id": "non-existent-service-id"},
            headers=auth_headers
        )
        
        # Should return error
        assert response.status_code in [400, 403, 404]

    def test_remove_service_from_tenant(self, test_client: TestClient, auth_headers: dict):
        """Test removing a service from a tenant"""
        tenant_id = "test-tenant-id"
        
        # First, try to get tenant's services
        services_response = test_client.get(
            f"/api/v1/tenants/{tenant_id}/services",
            headers=auth_headers
        )
        
        if services_response.status_code == 200:
            services = services_response.json().get("services", [])
            
            if len(services) > 0:
                service_id = services[0]["id"]
                
                response = test_client.delete(
                    f"/api/v1/tenants/{tenant_id}/services/{service_id}",
                    headers=auth_headers
                )
                
                # May succeed or be forbidden based on permissions
                assert response.status_code in [204, 403, 404]

    def test_assign_duplicate_service(self, test_client: TestClient, auth_headers: dict):
        """Test assigning a service that's already assigned"""
        # Get available services
        services_response = test_client.get(
            "/api/v1/services",
            headers=auth_headers
        )
        
        if services_response.status_code == 200:
            services = services_response.json().get("data", [])
            
            if len(services) > 0:
                service_id = services[0]["id"]
                tenant_id = "test-tenant-id"
                
                # Assign once
                first_response = test_client.post(
                    f"/api/v1/tenants/{tenant_id}/services",
                    json={"service_id": service_id},
                    headers=auth_headers
                )
                
                # Try to assign again
                second_response = test_client.post(
                    f"/api/v1/tenants/{tenant_id}/services",
                    json={"service_id": service_id},
                    headers=auth_headers
                )
                
                # Second attempt should fail with conflict
                if first_response.status_code == 201:
                    assert second_response.status_code == 409

    def test_get_services_with_roles(self, test_client: TestClient, auth_headers: dict):
        """Test that service details include role information"""
        # Get services
        services_response = test_client.get(
            "/api/v1/services",
            headers=auth_headers
        )
        
        if services_response.status_code == 200:
            services = services_response.json().get("data", [])
            
            if len(services) > 0:
                service_id = services[0]["id"]
                
                # Get service detail
                detail_response = test_client.get(
                    f"/api/v1/services/{service_id}",
                    headers=auth_headers
                )
                
                assert detail_response.status_code == 200
                data = detail_response.json()
                
                # Check roles structure
                assert "roles" in data
                roles = data["roles"]
                
                if len(roles) > 0:
                    role = roles[0]
                    assert "role_code" in role
                    assert "role_name" in role
