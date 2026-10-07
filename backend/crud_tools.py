import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_core.tools import tool

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in your environment or .env file.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@tool
def get_records(query: Optional[str] = None) -> str:
    """Fetch employee records from the database.
    If 'query' is provided, filters records where name, email, or department matches the search term.
    If 'query' is omitted or empty, fetches all records.
    """
    try:
        req = supabase.table("employees").select("*")
        if query and query.strip():
            clean_q = query.strip()
            req = req.or_(f"name.ilike.%{clean_q}%,email.ilike.%{clean_q}%,department.ilike.%{clean_q}%")
        
        response = req.execute()
        records = response.data
        if not records:
            return "No matching employee records found."
        return str(records)
    except Exception as e:
        return f"Error retrieving records: {str(e)}"


@tool
def create_record(name: str, department: str, position: str, email: str, phone: Optional[str] = None) -> str:
    """Add a new employee record into the database.
    Required fields: name, department, position, email.
    Optional field: phone.
    """
    try:
        payload = {
            "name": name,
            "department": department,
            "position": position,
            "email": email,
            "phone": phone
        }
        response = supabase.table("employees").insert(payload).execute()
        return f"Successfully created employee record: {response.data}"
    except Exception as e:
        return f"Error creating record: {str(e)}"


@tool
def update_record(
    employee_id: int,
    name: Optional[str] = None,
    department: Optional[str] = None,
    position: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> str:
    """Update an existing employee record by its numeric employee_id.
    Only provided fields will be modified.
    """
    try:
        updates = {}
        if name is not None:
            updates["name"] = name
        if department is not None:
            updates["department"] = department
        if position is not None:
            updates["position"] = position
        if email is not None:
            updates["email"] = email
        if phone is not None:
            updates["phone"] = phone

        if not updates:
            return "No fields provided to update."

        response = supabase.table("employees").update(updates).eq("id", employee_id).execute()
        if not response.data:
            return f"No employee found with ID {employee_id}."
        return f"Successfully updated employee record: {response.data}"
    except Exception as e:
        return f"Error updating record: {str(e)}"


@tool
def delete_record(employee_id: int) -> str:
    """Delete an employee record from the database by its numeric employee_id."""
    try:
        response = supabase.table("employees").delete().eq("id", employee_id).execute()
        if not response.data:
            return f"No employee found with ID {employee_id} to delete."
        return f"Successfully deleted employee record ID {employee_id}: {response.data}"
    except Exception as e:
        return f"Error deleting record: {str(e)}"


all_tools = [get_records, create_record, update_record, delete_record]
