-- This function calculates and returns the ancestors of a given topic.
-- The resultset includes the topic itself.
create or replace function get_topic_ancestors(topic_id integer)
returns table (
    id integer,
    name varchar(100)
    )
as
$$
    with recursive topic_tree(id, parent_id, name) as (
        select id, parent_id, name
            from lists_topictree
            where id = topic_id
        union all
        select ltt.id, ltt.parent_id, ltt.name
            from topic_tree tt
                inner join lists_topictree ltt
                on ltt.id = tt.parent_id
    )
    select id, name
        from topic_tree;
$$
language 'sql'
volatile;

-- This function calculates and returns the descendants of a given topic (depth-first search).
-- The resultset does not include the topic itself.
create or replace function get_topic_descendants(topic_id integer)
returns table (
    level integer,
    id integer,
    name varchar(100),
    path integer[]
    )
as
$$
    with recursive topic_tree(level, id, parent_id, name, path) as (
        select 1, id, parent_id, name, ARRAY[id] as path
            from lists_topictree
            where parent_id = topic_id
        union all
        select tt.level+1, ltt.id, ltt.parent_id, ltt.name, path || ltt.id
            from topic_tree tt
                inner join lists_topictree ltt
                on ltt.parent_id = tt.id
    )
    select level, id, name, path
        from topic_tree
        order by path;
$$
language 'sql'
volatile;
