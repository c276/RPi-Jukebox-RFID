import React from 'react';
import { useTranslation } from 'react-i18next';
import { TextField } from '@mui/material';

import { getActionAndCommand, getArgsValues } from '../../../utils';

const SelectPlaySpotify = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const { command } = getActionAndCommand(actionData);
  const values = getArgsValues(actionData);

  const song_url = values[0] || '';

  const handleChange = (event) => {
    const newUrl = event.target.value;
    handleActionDataChange('play_spotify', 'play_single', { song_url: newUrl });
  };

  return (
    <TextField
      fullWidth
      label={t('cards.controls.actions.play-spotify.input-label') || 'Spotify URI'}
      variant="outlined"
      value={song_url}
      onChange={handleChange}
      placeholder="spotify:track:xxx"
    />
  );
};

export default SelectPlaySpotify;