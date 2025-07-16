import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';

const Button = dynamic(() => import('../../components/Button'));

export default function PublishPage() {
  const { t } = useTranslation();
  const [taskId, setTaskId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [status, setStatus] = useState('');

  const submit = async () => {
    const metadata = { title, description, price: parseFloat(price) };
    const token = localStorage.getItem('token');
    const resp = await fetch(`/publish-tasks/${taskId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + token,
      },
      body: JSON.stringify(metadata),
    });
    if (!resp.ok) {
      setStatus(t('updateFailed'));
      return;
    }
    const retry = await fetch(`/publish-tasks/${taskId}/retry`, {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
    });
    setStatus(retry.ok ? t('publishScheduled') : t('updateFailed'));
  };

  return (
    <div className="space-y-2">
      <div>
        Task ID{' '}
        <input
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          className="border p-1"
        />
      </div>
      <div>
        Title{' '}
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="border p-1"
        />
      </div>
      <div>
        Description{' '}
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="border p-1"
        />
      </div>
      <div>
        Price{' '}
        <input
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          className="border p-1"
        />
      </div>
      <Button onClick={submit}>{t('updateAndPublish')}</Button>
      {status && <div>{status}</div>}
    </div>
  );
}

export const getStaticProps = async () => {
  return {
    props: {},
    revalidate: 60,
  };
};
