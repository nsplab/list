var AppDispatcher = require('../dispatchers/AppDispatcher.js');
var AppConstants = require('../constants/AppConstants.js');

var ApiKeyTypes = AppConstants.ApiKeyTypes;
var ServerActionTypes = AppConstants.ServerActionTypes;

module.exports = {
    responseForRequest: function(err, apikey, serverData) {
        var payload = {};
        var action_type = null;
        var err_action_type = null;
        switch(apikey) {
            case ApiKeyTypes.FETCH_LISTS:
                action_type = ServerActionTypes.FETCH_LISTS_SUCCESS;
                err_action_type = ServerActionTypes.FETCH_LISTS_ERROR;
                break;
            default:
                break;
        }
        if (err) {
            payload.actionType = err_action_type;
            payload.err = err;  // object w. keys: http_status_code
        } else {
            payload.actionType = action_type;
            payload.serverData = serverData;
        }
        console.debug(payload);
        if (action_type)
            AppDispatcher.dispatch(payload);
    }
};
