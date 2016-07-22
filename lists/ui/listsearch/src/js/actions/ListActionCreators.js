var AppDispatcher = require('../dispatchers/AppDispatcher.js');
var AppConstants = require('../constants/AppConstants.js');
var ApiUtils = require('../utils/ApiUtils.js');

var ActionTypes = AppConstants.ActionTypes;

var searchLists = function(topic, title) {
    AppDispatcher.dispatch({
        actionType: ActionTypes.FETCH_LISTS_PENDING
    });
    ApiUtils.searchLists(topic, title);
};

module.exports = {
    searchLists: searchLists
};
