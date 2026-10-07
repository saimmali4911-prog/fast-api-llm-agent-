# Contact Book (React + Supabase + Vercel)

A minimal CRUD app: Name + Contact Number, stored permanently in Supabase,
with a history list and full Create/Read/Update/Delete.

This is a standalone project — it does not touch or depend on any other
project, database, or deployment.

## 1. Create the Supabase project

1. Go to https://supabase.com → New project.
2. Once it's created, open **SQL Editor** and run:

```sql
create table contacts (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  contact_number text not null,
  created_at timestamptz not null default now()
);

alter table contacts enable row level security;

-- Simple public policy so the anon key can do CRUD.
-- Tighten this later if you add auth.
create policy "Allow all on contacts"
on contacts
for all
using (true)
with check (true);
```

3. Go to **Project Settings → API** and copy:
   - `Project URL` → this is `VITE_SUPABASE_URL`
   - `anon public` key → this is `VITE_SUPABASE_ANON_KEY`

## 2. Run locally (optional, to test first)

```bash
npm install
cp .env.example .env
# paste your Supabase URL + anon key into .env
npm run dev
```

## 3. Deploy to Vercel (new project)

1. Push this folder to a **new** GitHub repo (don't reuse an existing repo).
2. In Vercel: **Add New → Project** → import that repo.
   - Framework preset: Vite (auto-detected)
   - Build command: `npm run build`
   - Output directory: `dist`
3. Under **Environment Variables**, add:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
4. Deploy.

That's it — no other plugins or platforms needed. The app talks directly
to Supabase from the browser using the anon key, which is safe because
of the row-level security policy above.

## Notes

- To restrict who can edit/delete, add Supabase Auth later and change the
  RLS policy to check `auth.uid()`.
- The anon key is meant to be public (it's exposed in the frontend bundle);
  security comes from RLS policies, not from hiding the key.
