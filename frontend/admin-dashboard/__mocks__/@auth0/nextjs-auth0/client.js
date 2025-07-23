/* eslint-disable @typescript-eslint/no-require-imports */
module.exports = {
  withPageAuthRequired: (Component) => Component,
  UserProvider: ({ children }) => children,
  useUser: () => ({ user: exports.__user, isLoading: false }),
  __setUser: (u) => {
    exports.__user = u;
  },
};
