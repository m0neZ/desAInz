tRPC Usage Examples
===================

The admin dashboard communicates with the API Gateway using **tRPC**. Below is a minimal example showing how to create a query and mutation using the generated tRPC client.

.. code-block:: text

   // src/trpc.ts
   import { createTRPCReact } from '@trpc/react-query';
   import type { AppRouter } from '../server/router';

   export const trpc = createTRPCReact<AppRouter>();

.. code-block:: text

   // Example query inside a React component
   const Example: React.FC = () => {
       const { data, error } = trpc.trending.useQuery();
       if (error) return <p>Error: {error.message}</p>;
       return <pre>{JSON.stringify(data)}</pre>;
   };

.. code-block:: text

   // Example mutation
   const ApproveItem: React.FC<{id: string}> = ({ id }) => {
       const mutation = trpc.approve.useMutation();
       return (
           <button onClick={() => mutation.mutate({ id })}>
               Approve
           </button>
       );
   };
