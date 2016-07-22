var EventEmitter = require('events').EventEmitter;
var assign = require('react/lib/Object.assign');
//var _ = require('lodash');
var AppDispatcher = require('../dispatchers/AppDispatcher.js');
var AppConstants = require('../constants/AppConstants.js');

var ActionTypes = AppConstants.ActionTypes;
var ServerActionTypes = AppConstants.ServerActionTypes;

var CHANGE_EVENT = 'groupItems';

var _store = {
    actionType: null,
    isFetchPending: false,
    err: null,
    lists: []
};

var isArray = function(a) {
    return (!!a) && (a.constructor === Array);
};

var isObject = function(a) {
    return (!!a) && (a.constructor === Object);
};

var _populateLists = function(lists) {
    _store.lists = [];
    if (isArray(lists)) {
        _store.lists = lists.map(function(d) { return Object.assign({}, d); });
    }
};

var ListStore = assign({}, EventEmitter.prototype, {
    emitChange: function() {
        this.emit(CHANGE_EVENT);
    },
    addChangeListener: function(callback) {
        this.on(CHANGE_EVENT, callback);
    },
    removeChangeListener: function(callback) {
        this.removeListener(CHANGE_EVENT, callback);
    },
    getActionType: function() {
        return _store.actionType;
    },
    getError: function() {
        return _store.err;
    },
    getAll: function() {
        return _store;
    }
});

ListStore.dispatchToken = AppDispatcher.register(function(action) {
    var emit_change = true;
    switch(action.actionType) {
        // from server
        case ServerActionTypes.FETCH_LISTS_SUCCESS:
            _populateLists(action.serverData.lists);
            _store.err = null;
            _store.isFetchPending = false;
            break;
        case ServerActionTypes.FETCH_LISTS_ERROR:
            _store.err = action.err;
            break;
        // from client
        case ActionTypes.FETCH_LISTS_PENDING:
            _store.isFetchPending = true;
            break;
        default:
            emit_change = false;
            break;
    }
    if (emit_change) {
        console.debug('ListStore emitChange on actionType: ' + action.actionType);
        _store.actionType = action.actionType;
        ListStore.emitChange();
    }
});

module.exports = ListStore;
