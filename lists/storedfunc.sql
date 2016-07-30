-- topicedge join topicnode
create or replace view topic_connections as
    select t1.id as parent_id,
        t1.name as parent_name, 
        t1.description as parent_description,
        t2.id as child_id,
        t2.name as child_name,
        t2.description as child_description,
        e.id, e.description
    from lists_topicedge e
        inner join lists_topicnode t1 on t1.id = e.parent_id
        inner join lists_topicnode t2 on t2.id = e.child_id
;

-- This function calculates and returns the descendants of a given topic (depth-first search).
create or replace function get_topic_descendants(topic_id integer)
returns table (
    level integer,
    id integer,
    name varchar(100),
    path integer[]
    )
as
$$
    with recursive topic_paths(level, child_id, parent_id, name, path) as (
        select 1, child_id, parent_id, child_name, ARRAY[parent_id, child_id] as path
            from topic_connections
            where parent_id = topic_id
        union all
        select tp.level+1, tc.child_id, tc.parent_id, tc.child_name, path || tc.child_id
            from topic_paths tp
                inner join topic_connections tc
                on tc.parent_id = tp.child_id
    )
    select level, child_id, name, path
        from topic_paths
        order by path;
$$
language 'sql'
volatile;

-- This function calculates and returns the descendants of a given topic 
-- using depth-first search until a given child_topic
create or replace function get_topic_descendants_until(ancestor_topic_id integer, child_topic_id integer)
returns table (
    level integer,
    id integer,
    name varchar(100),
    path integer[]
    )
as
$$
    with recursive topic_paths(level, child_id, parent_id, name, path) as (
        select 1, child_id, parent_id, child_name, ARRAY[parent_id, child_id] as path
            from topic_connections
            where parent_id = ancestor_topic_id
        union all
        select tp.level+1, tc.child_id, tc.parent_id, tc.child_name, path || tc.child_id
            from topic_paths tp
                inner join topic_connections tc
                on tc.parent_id = tp.child_id
                and tp.child_id <> child_topic_id
    )
    select level, child_id, name, path
        from topic_paths
        where child_id = child_topic_id
        order by path;
$$
language 'sql'
volatile;
