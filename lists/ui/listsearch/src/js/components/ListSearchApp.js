var React = require('react');
var ListActionCreators = require('../actions/ListActionCreators.js');
var AppConstants = require('../constants/AppConstants.js');
var ListStore = require('../stores/ListStore.js');

var ServerActionTypes = AppConstants.ServerActionTypes;

var ListSearchForm = React.createClass({
    propTypes: {
        onSubmit: React.PropTypes.func.isRequired
    },
    getInitialState: function() {
        return {
            topic: '',
            title: ''
        };
    },
    onTopicChange: function(event) {
        this.setState({
            topic: event.target.value
        });
    },
    onTitleChange: function(event) {
        this.setState({
            title: event.target.value
        });
    },
    onSearchClick: function() {
        var topic = this.state.topic.trim();
        var title = this.state.title.trim();
        this.props.onSubmit(topic, title);
    },
    render: function() {
        var divStyle = {marginBottom: '2em'}; // replace with css class
        var topicInput = <input
            autoFocus={true}
            type="text"
            className="form-control"
            name="topic"
            placeholder="Topic name"
            value={this.state.topic}
            onChange={this.onTopicChange}
        />;
        var titleInput = <input
            type="text"
            className="form-control"
            name="title"
            placeholder="List title"
            value={this.state.title}
            onChange={this.onTitleChange}
        />;
        var searchBtn = <button
            type="button"
            className="btn btn-default btn-primary"
            onClick={this.onSearchClick}
            >Search
        </button>;
        return (
            <div style={divStyle}>
                <div className="form-group">
                    {topicInput}
                </div>
                <div className="form-group">
                    {titleInput}
                </div>
                {searchBtn}
            </div>
        );
    }
});

var ListSearchApp = React.createClass({
    propTypes: {
        detailRoute: React.PropTypes.string.isRequired
    },
    getInitialState: function() {
        return {
            lists: [],
            isPending: false
        };
    },
    componentDidMount: function() {
        ListStore.addChangeListener(this._onListStoreChange);
    },
    componentWillUnmount: function() {
        ListStore.removeChangeListener(this._onListStoreChange);
    },
    _handleOnSearch: function(topic, title) {
        ListActionCreators.searchLists(topic, title);
        this.setState({
            isPending: true
        });
    },
    _onListStoreChange: function() {
        var actionType = ListStore.getActionType();
        var err = null, new_state = null;
        switch(actionType) {
            case ServerActionTypes.FETCH_LISTS_SUCCESS:
                var store = ListStore.getAll();
                new_state = {
                    lists: store.lists,
                    isPending: false
                };
                break;
            case ServerActionTypes.FETCH_LISTS_ERROR:
                alert(actionType);
                new_state = {
                    lists: [],
                    isPending: false
                };
                break;
            default:
                break;
        }
        if (new_state) {
            this.setState(new_state);
        }
    },
    render: function() {
        var searchForm = <ListSearchForm
            onSubmit={this._handleOnSearch}
        />;
        var listRows = this.state.lists.map(function(list) {
            var listDetailHref = this.props.detailRoute + list.id + '/';
            return (
                <a href={listDetailHref} className="list-group-item" key={list.id}>
                    <h4 className="list-group-item-heading">{list.title}</h4>
                    <p className="list-group-item-text">{list.description}</p>
                    <p className="list-group-item-text text-muted">{list.topic__name}</p>
                </a>
            );
        }, this);
        var divStyle = {marginTop: '2em'};
        return (
            <div className="container" style={divStyle}>
                <div className="row">
                    <div className="col-md-8">
                        {searchForm}
                    </div>
                </div>
                <div className="row">
                    <div className="col-md-8">
                        <div className="list-group">
                            {listRows}
                        </div>
                    </div>
                </div>
            </div>
        );
    }
});

module.exports = ListSearchApp;
