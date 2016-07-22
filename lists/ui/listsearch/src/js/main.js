var ApiUtils = require('./utils/ApiUtils.js');
var ListSearchApp = require('./components/ListSearchApp.js');
var React = require('react');
var ReactDOM = require('react-dom');
window.React = React; // export for http://fb.me/react-devtools

ApiUtils.configureApi();
ReactDOM.render(<ListSearchApp
    detailRoute="/lists/"
    />,
    document.getElementById('app')
);
