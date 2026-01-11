#!/usr/bin/env python
"""
Demo script showing authorization middleware usage.

This script demonstrates key features of the authorization middleware
without needing to run the full FastAPI server.
"""

from app.middleware.authorization import (
    has_permission,
    is_admin,
    permission_cache,
)


def demo_permission_checking():
    """Demonstrate permission checking with various patterns."""
    print("=" * 60)
    print("PERMISSION CHECKING DEMO")
    print("=" * 60)
    
    # Example 1: Exact match
    print("\n1. Exact Permission Match:")
    user_perms = ["users.read", "users.write", "documents.read"]
    print(f"   User permissions: {user_perms}")
    print(f"   Has 'users.read'? {has_permission(user_perms, 'users.read')}")
    print(f"   Has 'users.delete'? {has_permission(user_perms, 'users.delete')}")
    
    # Example 2: Wildcard permissions
    print("\n2. Wildcard Permissions:")
    user_perms = ["users.*", "documents.read"]
    print(f"   User permissions: {user_perms}")
    print(f"   Has 'users.read'? {has_permission(user_perms, 'users.read')}")
    print(f"   Has 'users.write'? {has_permission(user_perms, 'users.write')}")
    print(f"   Has 'users.delete'? {has_permission(user_perms, 'users.delete')}")
    print(f"   Has 'documents.write'? {has_permission(user_perms, 'documents.write')}")
    
    # Example 3: Admin wildcard (all permissions)
    print("\n3. Admin Wildcard (All Permissions):")
    user_perms = ["*"]
    print(f"   User permissions: {user_perms}")
    print(f"   Has 'users.read'? {has_permission(user_perms, 'users.read')}")
    print(f"   Has 'admin.delete'? {has_permission(user_perms, 'admin.delete')}")
    print(f"   Has 'any.permission.here'? {has_permission(user_perms, 'any.permission.here')}")
    
    # Example 4: Nested wildcard
    print("\n4. Nested Wildcard Permissions:")
    user_perms = ["admin.*.view"]
    print(f"   User permissions: {user_perms}")
    print(f"   Has 'admin.settings.view'? {has_permission(user_perms, 'admin.settings.view')}")
    print(f"   Has 'admin.users.view'? {has_permission(user_perms, 'admin.users.view')}")
    print(f"   Has 'admin.settings.edit'? {has_permission(user_perms, 'admin.settings.edit')}")


def demo_admin_roles():
    """Demonstrate admin role detection."""
    print("\n" + "=" * 60)
    print("ADMIN ROLE DETECTION DEMO")
    print("=" * 60)
    
    print("\n1. Admin Roles:")
    print(f"   Is ['admin'] admin? {is_admin(['admin'])}")
    print(f"   Is ['super_admin'] admin? {is_admin(['super_admin'])}")
    print(f"   Is ['system_admin'] admin? {is_admin(['system_admin'])}")
    
    print("\n2. Non-Admin Roles:")
    print(f"   Is ['user'] admin? {is_admin(['user'])}")
    print(f"   Is ['editor', 'viewer'] admin? {is_admin(['editor', 'viewer'])}")
    
    print("\n3. Mixed Roles:")
    print(f"   Is ['user', 'admin'] admin? {is_admin(['user', 'admin'])}")


def demo_permission_cache():
    """Demonstrate permission caching."""
    print("\n" + "=" * 60)
    print("PERMISSION CACHING DEMO")
    print("=" * 60)
    
    # Clear cache first
    permission_cache.clear()
    
    print("\n1. Cache Operations:")
    user_id = "user-123"
    tenant_id = "tenant-123"
    permissions = ["users.read", "users.write", "documents.read"]
    
    print(f"   Setting cache for {user_id} in {tenant_id}")
    permission_cache.set(user_id, tenant_id, permissions)
    
    cached = permission_cache.get(user_id, tenant_id)
    print(f"   Retrieved from cache: {cached}")
    print(f"   Match: {cached == permissions}")
    
    print("\n2. Cache Invalidation:")
    print(f"   Invalidating cache for {user_id}")
    permission_cache.invalidate(user_id, tenant_id)
    cached = permission_cache.get(user_id, tenant_id)
    print(f"   After invalidation: {cached}")
    
    print("\n3. Tenant Isolation:")
    permission_cache.set("user-1", "tenant-1", ["users.read"])
    permission_cache.set("user-1", "tenant-2", ["documents.read"])
    
    tenant1_perms = permission_cache.get("user-1", "tenant-1")
    tenant2_perms = permission_cache.get("user-1", "tenant-2")
    
    print(f"   User-1 in tenant-1: {tenant1_perms}")
    print(f"   User-1 in tenant-2: {tenant2_perms}")
    print(f"   Properly isolated: {tenant1_perms != tenant2_perms}")
    
    # Clean up
    permission_cache.clear()


def demo_use_cases():
    """Demonstrate common use cases."""
    print("\n" + "=" * 60)
    print("COMMON USE CASES")
    print("=" * 60)
    
    print("\n1. User Management System:")
    user_permissions = ["users.read", "users.write"]
    print(f"   User permissions: {user_permissions}")
    print(f"   Can view users? {has_permission(user_permissions, 'users.read')}")
    print(f"   Can create users? {has_permission(user_permissions, 'users.write')}")
    print(f"   Can delete users? {has_permission(user_permissions, 'users.delete')}")
    
    print("\n2. Document System with Hierarchical Permissions:")
    user_permissions = ["documents.*"]
    print(f"   User permissions: {user_permissions}")
    print(f"   Can read documents? {has_permission(user_permissions, 'documents.read')}")
    print(f"   Can write documents? {has_permission(user_permissions, 'documents.write')}")
    print(f"   Can share documents? {has_permission(user_permissions, 'documents.share')}")
    
    print("\n3. Admin Dashboard:")
    admin_user = {"roles": ["admin"], "permissions": []}
    regular_user = {"roles": ["user"], "permissions": ["dashboard.view"]}
    
    print(f"   Admin user can access? {is_admin(admin_user['roles'])}")
    print(f"   Regular user can access? {is_admin(regular_user['roles'])}")
    print(f"   Regular user has dashboard permission? {has_permission(regular_user['permissions'], 'dashboard.view')}")


def main():
    """Run all demos."""
    print("\n")
    print("*" * 60)
    print("AUTHORIZATION MIDDLEWARE DEMONSTRATION")
    print("*" * 60)
    
    demo_permission_checking()
    demo_admin_roles()
    demo_permission_cache()
    demo_use_cases()
    
    print("\n" + "*" * 60)
    print("DEMO COMPLETE")
    print("*" * 60)
    print("\nFor more information, see:")
    print("  - AUTHORIZATION.md - Complete documentation")
    print("  - app/api/examples_authorization.py - FastAPI route examples")
    print("  - tests/test_authorization*.py - Comprehensive tests")
    print()


if __name__ == "__main__":
    main()
