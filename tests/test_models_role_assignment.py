"""
ロール割り当てモデルのユニットテスト

テスト対象:
- RoleAssignment
- RoleAssignmentCreate
- Role
"""
import pytest
import json
from datetime import datetime
from pydantic import ValidationError

from app.models.role_assignment import RoleAssignment, RoleAssignmentCreate, Role


class TestRoleAssignmentModel:
    """RoleAssignmentモデルのテストクラス"""
    
    class Test正常系:
        """正常系テスト"""
        
        def test_role_assignment_正常な作成(self):
            """TC-MODEL-RA-001"""
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            
            assert role_assignment.tenant_id == "tenant-test"
            assert role_assignment.user_id == "user_test_001"
            assert role_assignment.service_id == "auth-service"
            assert role_assignment.role_name == "全体管理者"
            assert role_assignment.assigned_by == "user_admin"
            assert role_assignment.type == "role_assignment"
            assert role_assignment.id.startswith("role_assignment_")
            assert isinstance(role_assignment.assigned_at, datetime)
            assert isinstance(role_assignment.created_at, datetime)
        
        def test_role_assignment_デフォルト値の設定(self):
            """TC-MODEL-RA-002"""
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            
            assert role_assignment.id.startswith("role_assignment_")
            assert role_assignment.type == "role_assignment"
            assert isinstance(role_assignment.assigned_at, datetime)
            assert isinstance(role_assignment.created_at, datetime)
            now = datetime.utcnow()
            assert (now - role_assignment.assigned_at).total_seconds() < 5
            assert (now - role_assignment.created_at).total_seconds() < 5
        
        def test_role_assignment_エイリアスによるシリアライズ(self):
            """TC-MODEL-RA-003"""
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            
            serialized = role_assignment.model_dump(by_alias=True)
            
            assert "tenantId" in serialized
            assert "userId" in serialized
            assert "serviceId" in serialized
            assert "roleName" in serialized
            assert "assignedBy" in serialized
            assert "assignedAt" in serialized
            assert "createdAt" in serialized
            assert serialized["tenantId"] == "tenant-test"
            assert serialized["userId"] == "user_test_001"
            assert serialized["serviceId"] == "auth-service"
            assert serialized["roleName"] == "全体管理者"
        
        def test_role_assignment_datetimeのISO形式変換(self):
            """TC-MODEL-RA-004"""
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            
            json_str = role_assignment.model_dump_json(by_alias=True)
            parsed = json.loads(json_str)
            
            assert parsed["assignedAt"].endswith("Z")
            assert parsed["createdAt"].endswith("Z")
            assert "T" in parsed["assignedAt"]
            assert "T" in parsed["createdAt"]
    
    class Test異常系:
        """異常系テスト"""
        
        def test_role_assignment_必須フィールド欠損_tenant_id(self):
            """TC-MODEL-RA-E-001"""
            with pytest.raises(ValidationError):
                RoleAssignment(
                    user_id="user_test_001",
                    service_id="auth-service",
                    role_name="全体管理者",
                    assigned_by="user_admin",
                )
        
        def test_role_assignment_必須フィールド欠損_user_id(self):
            """TC-MODEL-RA-E-002"""
            with pytest.raises(ValidationError):
                RoleAssignment(
                    tenant_id="tenant-test",
                    service_id="auth-service",
                    role_name="全体管理者",
                    assigned_by="user_admin",
                )
        
        def test_role_assignment_必須フィールド欠損_service_id(self):
            """TC-MODEL-RA-E-003"""
            with pytest.raises(ValidationError):
                RoleAssignment(
                    tenant_id="tenant-test",
                    user_id="user_test_001",
                    role_name="全体管理者",
                    assigned_by="user_admin",
                )
        
        def test_role_assignment_必須フィールド欠損_role_name(self):
            """TC-MODEL-RA-E-004"""
            with pytest.raises(ValidationError):
                RoleAssignment(
                    tenant_id="tenant-test",
                    user_id="user_test_001",
                    service_id="auth-service",
                    assigned_by="user_admin",
                )
        
        def test_role_assignment_必須フィールド欠損_assigned_by(self):
            """TC-MODEL-RA-E-005"""
            with pytest.raises(ValidationError):
                RoleAssignment(
                    tenant_id="tenant-test",
                    user_id="user_test_001",
                    service_id="auth-service",
                    role_name="全体管理者",
                )
        
        def test_role_assignment_空文字列のservice_id(self):
            """TC-MODEL-RA-E-006"""
            # Pydanticは空文字列を許容するため、インスタンス化は成功するが
            # ビジネスロジックでは無効として扱われる
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            assert role_assignment.service_id == ""
        
        def test_role_assignment_空文字列のrole_name(self):
            """TC-MODEL-RA-E-007"""
            # Pydanticは空文字列を許容するため、インスタンス化は成功するが
            # ビジネスロジックでは無効として扱われる
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="",
                assigned_by="user_admin",
            )
            assert role_assignment.role_name == ""
    
    class Test境界値:
        """境界値テスト"""
        
        def test_role_assignment_最大長のservice_id(self):
            """TC-MODEL-RA-B-001"""
            long_service_id = "a" * 255
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id=long_service_id,
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            assert role_assignment.service_id == long_service_id
            assert len(role_assignment.service_id) == 255
        
        def test_role_assignment_最大長のrole_name(self):
            """TC-MODEL-RA-B-002"""
            long_role_name = "ロ" * 100
            role_assignment = RoleAssignment(
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name=long_role_name,
                assigned_by="user_admin",
            )
            assert role_assignment.role_name == long_role_name
            assert len(role_assignment.role_name) == 100


class TestRoleAssignmentCreateModel:
    """RoleAssignmentCreateモデルのテストクラス"""
    
    class Test正常系:
        """正常系テスト"""
        
        def test_role_assignment_create_正常な作成(self):
            """TC-MODEL-RAC-001"""
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="auth-service",
                role_name="全体管理者",
            )
            
            assert data.tenant_id == "tenant-test"
            assert data.service_id == "auth-service"
            assert data.role_name == "全体管理者"
        
        def test_role_assignment_create_エイリアスによるデシリアライズ(self):
            """TC-MODEL-RAC-002"""
            camel_case_data = {
                "tenantId": "tenant-test",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
            }
            
            data = RoleAssignmentCreate(**camel_case_data)
            
            assert data.tenant_id == "tenant-test"
            assert data.service_id == "auth-service"
            assert data.role_name == "全体管理者"
    
    class Test異常系:
        """異常系テスト"""
        
        def test_role_assignment_create_必須フィールド欠損_tenant_id(self):
            """TC-MODEL-RAC-E-001"""
            with pytest.raises(ValidationError):
                RoleAssignmentCreate(
                    service_id="auth-service",
                    role_name="全体管理者",
                )
        
        def test_role_assignment_create_必須フィールド欠損_service_id(self):
            """TC-MODEL-RAC-E-002"""
            with pytest.raises(ValidationError):
                RoleAssignmentCreate(
                    tenant_id="tenant-test",
                    role_name="全体管理者",
                )
        
        def test_role_assignment_create_必須フィールド欠損_role_name(self):
            """TC-MODEL-RAC-E-003"""
            with pytest.raises(ValidationError):
                RoleAssignmentCreate(
                    tenant_id="tenant-test",
                    service_id="auth-service",
                )


class TestRoleModel:
    """Roleモデルのテストクラス"""
    
    class Test正常系:
        """正常系テスト"""
        
        def test_role_正常な作成(self):
            """TC-MODEL-R-001"""
            role = Role(
                service_id="auth-service",
                role_name="全体管理者",
                description="ユーザー登録・削除、ロール割り当て",
            )
            
            assert role.service_id == "auth-service"
            assert role.role_name == "全体管理者"
            assert role.description == "ユーザー登録・削除、ロール割り当て"
        
        def test_role_エイリアスによるシリアライズ(self):
            """TC-MODEL-R-002"""
            role = Role(
                service_id="auth-service",
                role_name="全体管理者",
                description="ユーザー登録・削除、ロール割り当て",
            )
            
            serialized = role.model_dump(by_alias=True)
            
            assert "serviceId" in serialized
            assert "roleName" in serialized
            assert "description" in serialized
            assert serialized["serviceId"] == "auth-service"
            assert serialized["roleName"] == "全体管理者"
    
    class Test異常系:
        """異常系テスト"""
        
        def test_role_必須フィールド欠損_service_id(self):
            """TC-MODEL-R-E-001"""
            with pytest.raises(ValidationError):
                Role(
                    role_name="全体管理者",
                    description="説明",
                )
        
        def test_role_必須フィールド欠損_role_name(self):
            """TC-MODEL-R-E-002"""
            with pytest.raises(ValidationError):
                Role(
                    service_id="auth-service",
                    description="説明",
                )
        
        def test_role_必須フィールド欠損_description(self):
            """TC-MODEL-R-E-003"""
            with pytest.raises(ValidationError):
                Role(
                    service_id="auth-service",
                    role_name="全体管理者",
                )
