import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import { usePublishTasks } from '../../lib/trpc/hooks';

function PublishPage() {
  const { t } = useTranslation();
  const { data: tasks, isLoading } = usePublishTasks();

  return (
    <div className="space-y-2">
      <h1>{t('publishTasks')}</h1>
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
