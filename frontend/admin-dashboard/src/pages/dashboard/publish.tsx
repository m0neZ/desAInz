import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { trpc, type PublishTask } from '../../trpc';

export default function PublishPage() {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState<PublishTask[]>([]);

  useEffect(() => {
    async function load() {
      setTasks(await trpc.publishTasks.list());
    }
    void load();
  }, []);

  return (
    <div className="space-y-2">
      <h1>{t('publishTasks')}</h1>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            {task.title} - {task.status}
          </li>
        ))}
      </ul>
    </div>
  );
}

export const getStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
