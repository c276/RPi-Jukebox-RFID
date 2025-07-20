import React from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';

import AddIcon from '@mui/icons-material/Add';
import CardsList from './list';
import Fab from '@mui/material/Fab';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

import Header from '../Header';

const CardsOverview = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { t } = useTranslation();

  const openRegisterCard = () => {
    navigate('register');
  };

  // 🔧 Static card data (mocked)
  const staticCards = {
    card1: {
      action: {
        args: { song_url: 'https://open.spotify.com/track/abc123' }
      },
      from_alias: 'play_single'
    },
    card2: {
      action: {
        args: { folder_path: '/music/album2' }
      },
      from_alias: 'play_folder'
    },
    card3: {
      action: {
        args: { album_id: 'album_xyz' }
      },
      from_alias: 'play_album'
    }
  };

  return (
    <Grid container id="cards">
      <Header title={t('cards.overview.cards')} />
      <Grid
        container
        spacing={1}
        sx={{
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <CardsList cardsList={staticCards} />
      </Grid>
      <Fab
        aria-label={t('cards.overview.register-card')}
        color="primary"
        onClick={openRegisterCard}
        sx={{
          position: 'fixed',
          bottom: '76px',
          right: theme.spacing(2),
        }}
      >
        <AddIcon />
      </Fab>
    </Grid>
  );
};

export default CardsOverview;
