import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { getActionAndCommand, getArgsValues } from '../../../utils';

const SelectPlaySpotify = ({
  actionData,
  registerMusicToCard,
  // handleActionDataChange,
  // cardId,
}) => {
  const { t } = useTranslation();
  const { command } = getActionAndCommand(actionData);
  const [inputValue, setInputValue] = useState('');

  const handleChange = (event) => {
    const value = event.target.value;
    // setInputValue(value);
    registerMusicToCard('play_single', { song_url: value });
  }

  return (
    <input
      type="text"
      placeholder="Enter spotify uri"
      value={inputValue}
      onChange={handleChange}
    />
  );
};

export default SelectPlaySpotify;
