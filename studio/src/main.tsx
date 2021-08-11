import React from 'react';
import ReactDOM from 'react-dom';

// This import has to come first for CSS reasons.
import 'studio/components/Studio.css';

import App from 'studio/components/App';

ReactDOM.render(
  <App/>,
  document.getElementById('studioRoot'),
);
