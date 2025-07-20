import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { useTranslation } from 'react-i18next';

import CardsForm from './form';
import {
  buildActionData,
  findActionByCommand,
} from './utils';

const CardsEdit = () => {
  const { t } = useTranslation();
  const { cardId } = useParams();
  const [actionData, setActionData] = useState({});

  // Define a static list of cards (mocked data)
  const staticCardsList = {
    'card1': {
      action: {
        args: { song_url: 'https://open.spotify.com/track/example1' }
      },
      from_alias: 'play_single'
    },
    'card2': {
      action: {
        args: { folder_path: '/music/folder2' }
      },
      from_alias: 'play_folder'
    }
    // add more cards as needed
  };

  useEffect(() => {
    if (cardId && staticCardsList[cardId]) {
      const {
        action: { args },
        from_alias: command
      } = staticCardsList[cardId];

      const action = findActionByCommand(command);
      const actionData = buildActionData(action, command, args);

      setActionData(actionData);
    }
  }, [cardId]);

  return (
    <CardsForm
      title={t('cards.edit.edit-card')}
      cardId={cardId}
      actionData={actionData}
      setActionData={setActionData}
    />
  );
};

export default CardsEdit;
