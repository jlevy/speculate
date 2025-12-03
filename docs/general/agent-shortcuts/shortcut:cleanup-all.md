# Shortcut: Clean Up Code

Instructions:

Run full format/typecheck/lint/test cycle and review code following
@shortcut:precommit-process.md.

Then do the following additional cleanup steps, running tests and fixing issues after
each step:

1. Duplicate types: Review the code for any types that you have defined and find if
   there are any duplicates and remove or consolidate them.

2. Duplicate Components: Review the recent changes for duplicate components where we can
   reuse.

3. Duplicate code: Review the code base for any duplicate code and refactor it to reduce
   duplication.

4. Review Types and use actual types over any

   - Don’t create explicit TypeScript interfaces with `any` types—either use proper
     types from your data sources or let TypeScript infer types automatically, so type
     safety flows through your codebase instead of forcing defensive checks everywhere.

   - Look for interfaces where most/all properties are `any`—delete them and use
     inferred return types or properly type each property from its source.

5. Review Types and eliminate as much of optionals as possible so we don’t conditionally
   leak optional state all through out the codebase

6. Dead code: Review the code base for any dead code and remove it.

7. Follow instructions in @shortcut:cleanup-remove-trivial-tests.md to remove any
   trivial tests.

8. Follow instructions in @shortcut:cleanup-update-docstrings.md to ensure all
   docstrings are up to date and clear.

9. Review Settings.ts and find any Constants and find any constants that should be in
   there

10. Remove unused parameters.
    Find any functions/components with parameters that are not being called and remove
    them.

11. clean up code that was created in process of debuging

12. Performance: Fix N+1 queries and sequential async operations

    - Replace `for` loops with sequential `await` with `Promise.all` for parallel
      execution

    - Batch database queries instead of individual fetches in loops

    - Consolidate nested sequential queries into single `Promise.all` call

    - Reference: commit `0a6d1326` (5 sequential → 1 parallel query)
