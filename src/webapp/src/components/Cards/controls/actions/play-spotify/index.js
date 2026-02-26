import React from 'react';
import { useTranslation } from 'react-i18next';
import { TextField } from '@mui/material';

import { getActionAndCommand, getArgsValues } from '../../../utils';

const SelectPlaySpotify = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const values = getArgsValues(actionData);

  const song_url = values[0] || '';

  const handleChange = (event) => {
    newUrl = event.target.value;
    // expected_ https://open.spotify.com/playlist/04paTgaKcuPEs4eCJOKGd5?si=MHXqyuZ0TJO24zztCaIeQQ
    // apply regex pattern to extract the URI 
    // spotify:playlist:04paTgaKcuPEs4eCJOKGd5
    const regex = /spotify:(track|album|playlist|artist):[a-zA-Z0-9]+|https:\/\/open\.spotify\.com\/(track|album|playlist|artist)\/[a-zA-Z0-9]+/;
    const match = newUrl.match(regex);
    // print the match    
    console.log('match', match);
    if (match) {
      newUrl = match[0].startsWith('spotify:') ? match[0] : match[0].replace('https://open.spotify.com/', 'spotify:').replace('/', ':');
    }
    handleActionDataChange('play_spotify', 'play_spotify', { song_url: newUrl });
  };

  return (
    <TextField
      fullWidth
      label="Spotify URI"
      variant="outlined"
      value={song_url}
      onChange={handleChange}
      placeholder="https://open.spotify.com/playlist/123456789?si=abcde12345"
    />
  );
};

export default SelectPlaySpotify;