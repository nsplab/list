var ServerActionCreators = require('../actions/ServerActionCreators.js');
var AppConstants = require('../constants/AppConstants.js');

var ApiKeyTypes = AppConstants.ApiKeyTypes;

var HOST = 'localhost';
var PROTOCOL = 'http:';

var configureApi = function() {
    PROTOCOL = window.location.protocol;
    HOST = window.location.hostname + (window.location.port ? ':' + window.location.port: '');
};

var make_api_url = function(part) {
    return PROTOCOL + '//' + HOST + '/listapp/' + part;
};

var getRequest = function(key, req_url, callback) {
    /*
     * @param {String} key - ApiKeyTypes value
     * @param {String} req_url - full URL
     * @param {function} callback for the xhr
     */
    console.debug('GET: ' + req_url);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', req_url);
    xhr.onreadystatechange = function() {
        var data;
        if (xhr.readyState == 4) {
            console.debug('Status code: ' + xhr.status);
            if (xhr.status == 200) {
                data = JSON.parse(xhr.responseText);
                callback(null, key, data);
            } else {
                data = {
                    http_status_code: xhr.status,
                    error_message: ''
                };
                if (xhr.responseText.length) {
                    try {
                        var ed = JSON.parse(xhr.responseText);
                        data['error_message'] = ed['error_message'];
                    } catch (e) {
                        data['error_message'] = '';
                    }
                }
                callback(data, key, null);
            }
        }
    }
    xhr.send();
};

module.exports = {
    configureApi: configureApi,
    searchLists: function(topic, title) {
        var req_url = make_api_url('list/search/');
        if (topic.length && title.length) {
            req_url = req_url + '?topic=' + topic;
            req_url = req_url + '&title=' + title;
        } else if (topic.length) {
            req_url = req_url + '?topic=' + topic;
        } else if (title.length) {
            req_url = req_url + '?title=' + title;
        }
        getRequest(ApiKeyTypes.FETCH_LISTS,
            req_url,
            ServerActionCreators.responseForRequest
        );
    }
};
