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
  const name = values[1] || '';

  const handleChangeUrl = (event) => {
    let newUrl = event.target.value;
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
    if (name) {
      newUrl = `${newUrl}#${name}`;
    }
    handleActionDataChange('play_spotify', 'play_spotify', { song_url: newUrl, name });
  };

  const handleChangeName = (event) => {
    const newName = event.target.value;
    let newUrl = song_url;
    if (newUrl && newName) {
      newUrl = `${newUrl.split('#')[0]}#${newName}`;
    }
    handleActionDataChange('play_spotify', 'play_spotify', { song_url: newUrl, name: newName });
  };

  return (
    <>
      <TextField
        fullWidth
        label="Spotify URI"
        variant="outlined"
        value={song_url}
        onChange={handleChangeUrl}
        placeholder="https://open.spotify.com/playlist/123456789?si=abcde12345"
      />
      <TextField
        fullWidth
        label="Name"
        variant="outlined"
        value={name}
        onChange={handleChangeName}
        placeholder="Spotify Song Name (optional)"
        style={{ marginTop: '0.5rem' }}
      />
    </>
  );
};

export default SelectPlaySpotify;