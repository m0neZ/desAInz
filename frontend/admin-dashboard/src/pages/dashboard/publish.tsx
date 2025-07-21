// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import { usePublishTasks } from '../../lib/trpc/hooks';
import { useRouter } from 'next/router';

function PublishPage() {
  const { t } = useTranslation();
  const { data: tasks, isLoading } = usePublishTasks();
  const { query } = useRouter();
  const mockupId = query.mockupId as string | undefined;

  return (
    <div className="space-y-2">
      <h1>{t('publishTasks')}</h1>
      {mockupId && (
        <p data-testid="selected-mockup">Publishing mockup {mockupId}</p>
      )}
      {isLoading || !tasks ? (
        <div>{t('loading')}</div>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              {task.title} - {task.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const getStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
export default withPageAuthRequired(PublishPage);
