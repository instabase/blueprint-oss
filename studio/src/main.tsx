import React from 'react';
import ReactDOM from 'react-dom';

// These imports has to come first for CSS reasons.
import 'studio/components/Theme.css';
import 'studio/components/Studio.css';

import App from 'studio/components/App';

ReactDOM.render(
  <App/>,
  document.getElementById('studioRoot'),
);
