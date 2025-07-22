// @flow
const React = require('react');

/*::
type UserProviderProps = {
  children: React.Node,
};
*/

module.exports = {
  withPageAuthRequired: (Component /*: React.ComponentType<any> */) => Component,
  UserProvider: ({ children } /*: UserProviderProps */) => children,
};

