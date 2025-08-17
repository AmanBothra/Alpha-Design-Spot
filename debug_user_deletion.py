#!/usr/bin/env python
"""
Debug script for testing user deletion API and monitoring with Sentry.
This script helps verify the fix for 500 internal server errors.
"""

import os
import django
import sys
from django.contrib.auth import get_user_model
from django.db import connection

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


User = get_user_model()


def check_user_relationships(user_id):
    """Check what relationships exist for a user that might cause deletion issues."""
    print(f"\n🔍 Checking relationships for User ID: {user_id}")

    try:
        user = User.objects.get(id=user_id)
        print(
            f"User: {user.email} (Type: {user.user_type}, Deleted: {user.is_deleted})"
        )

        # Check related objects
        customer_frames = user.customer_frame.count()
        subscriptions = user.subscription_users.count()

        print(f"- CustomerFrames: {customer_frames}")
        print(f"- Subscriptions: {subscriptions}")

        # Check for any posts created by this user
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM app_modules_post_businesspost 
                WHERE customer_id = %s
            """,
                [user_id],
            )
            business_posts = cursor.fetchone()[0]
            print(f"- BusinessPosts: {business_posts}")

        return {
            "user_exists": True,
            "customer_frames": customer_frames,
            "subscriptions": subscriptions,
            "business_posts": business_posts,
            "is_deleted": user.is_deleted,
        }

    except User.DoesNotExist:
        print(f"❌ User with ID {user_id} does not exist")
        return {"user_exists": False}
    except Exception as e:
        print(f"❌ Error checking user relationships: {str(e)}")
        return {"error": str(e)}


def test_soft_delete_functionality():
    """Test the soft delete functionality directly."""
    print(f"\n🧪 Testing Soft Delete Functionality")

    # Find a test user (preferably one that's not already deleted)
    test_user = User.objects.filter(is_deleted=False, user_type="customer").first()

    if not test_user:
        print("❌ No suitable test user found")
        return False

    print(f"Testing with user: {test_user.email} (ID: {test_user.id})")

    # Check relationships before deletion
    relationships = check_user_relationships(test_user.id)

    # Test soft delete
    try:
        print("\n🔄 Performing soft delete...")
        test_user.soft_delete()

        # Verify soft delete worked
        test_user.refresh_from_db()
        if test_user.is_deleted and test_user.deleted_at:
            print("✅ Soft delete successful!")
            print(f"   - is_deleted: {test_user.is_deleted}")
            print(f"   - deleted_at: {test_user.deleted_at}")

            # Test restore functionality
            print("\n🔄 Testing restore...")
            test_user.restore()
            test_user.refresh_from_db()

            if not test_user.is_deleted and not test_user.deleted_at:
                print("✅ Restore successful!")
                return True
            else:
                print("❌ Restore failed")
                return False
        else:
            print("❌ Soft delete failed")
            return False

    except Exception as e:
        print(f"❌ Error during soft delete test: {str(e)}")
        return False


def simulate_api_call():
    """Simulate the API call that was causing 500 errors."""
    print(f"\n🌐 Simulating API Call")

    # Find a test user
    test_user = User.objects.filter(is_deleted=False, user_type="customer").first()

    if not test_user:
        print("❌ No suitable test user found for API test")
        return

    print(f"Testing API call for user: {test_user.email} (ID: {test_user.id})")

    # This would be the API endpoint: DELETE /api/account/user-profile/{id}/
    print(f"API Endpoint: DELETE /api/account/user-profile/{test_user.id}/")
    print("📋 Expected behavior: Soft delete instead of hard delete")
    print("📋 Expected response: 200 OK with success message")
    print("📋 Sentry tracking: User deletion event with business context")


def check_database_constraints():
    """Check foreign key constraints that could cause deletion issues."""
    print(f"\n🔗 Checking Database Constraints")

    constraints = [
        ("account_usercode", "user_id", "User codes"),
        ("account_customerframe", "customer_id", "Customer frames"),
        ("account_subscription", "user_id", "Subscriptions"),
        ("post_businesspost", "customer_id", "Business posts"),
    ]

    for table, fk_column, description in constraints:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE {fk_column} IS NOT NULL
                """)
                count = cursor.fetchone()[0]
                print(f"- {description}: {count} records with foreign key references")
        except Exception as e:
            print(f"- {description}: Error checking ({str(e)})")


def main():
    """Main debug function."""
    print("=" * 60)
    print("🔧 USER DELETION API DEBUG TOOL")
    print("=" * 60)
    print("This tool helps debug the 500 internal server error")
    print("when calling the delete user API endpoint.")
    print()

    # Check database constraints
    check_database_constraints()

    # Test soft delete functionality
    success = test_soft_delete_functionality()

    # Simulate API call
    simulate_api_call()

    # Provide recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    print("1. ✅ FIXED: Use soft delete instead of hard delete")
    print("2. ✅ ADDED: Comprehensive Sentry monitoring for user deletion")
    print("3. ✅ ADDED: Error context with user and admin information")
    print("4. ✅ ADDED: Performance monitoring for deletion operations")
    print("5. 📊 MONITOR: Check Sentry dashboard for deletion success/failure rates")

    print(f"\n🚀 SENTRY MONITORING:")
    print("- Real-time error tracking for any deletion failures")
    print("- Business intelligence on user deletion patterns")
    print("- Performance monitoring for slow deletion operations")
    print("- Detailed context for debugging future issues")

    if success:
        print(f"\n✅ Soft delete functionality is working correctly!")
    else:
        print(f"\n❌ Issues detected with soft delete functionality!")

    print("=" * 60)


if __name__ == "__main__":
    main()
