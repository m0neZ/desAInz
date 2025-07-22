// @flow
/* eslint-disable @typescript-eslint/no-require-imports */
/* flowlint unclear-type:off */
const React = require('react');
void React;

type UserProviderProps = {
  children: React.Node,
};
module.exports = {
  withPageAuthRequired: (Component: React.ComponentType<mixed>) => Component,
  UserProvider: ({ children }: UserProviderProps) => children,
};
