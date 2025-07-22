// @flow
import * as React from 'react';

export type UserProviderProps = {|
  children: React.Node,
|};

module.exports = {
  withPageAuthRequired: <P>(
    Component: React.ComponentType<P>
  ): React.ComponentType<P> => Component,
  UserProvider: ({ children }: UserProviderProps): React.Node => children,
};
