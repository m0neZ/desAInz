// @flow
import React from 'react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useTranslation } from 'react-i18next';
import { usePublishTasks } from '../../lib/trpc/hooks';
import { useState } from 'react';
import { useRouter } from 'next/router';

function PublishPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const limit = 50;
  const { data: tasks, isLoading } = usePublishTasks(limit, page);
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
      <div className="space-x-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
          Prev
        </button>
        <button onClick={() => setPage(page + 1)}>Next</button>
      </div>
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
