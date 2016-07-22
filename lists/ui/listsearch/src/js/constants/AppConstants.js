var keyMirror = require('keymirror'); // use all lowercase to match package.json

module.exports = {
    ApiKeyTypes: keyMirror({
        FETCH_LISTS: null,
    }),
    ActionTypes: keyMirror({
        FETCH_LISTS_PENDING: null,
    }),
    ServerActionTypes: keyMirror({
        FETCH_LISTS_ERROR: null,
        FETCH_LISTS_SUCCESS: null,
    })
};
