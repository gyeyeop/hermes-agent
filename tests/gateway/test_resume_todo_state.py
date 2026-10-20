"""``session.resume`` carries the session's todo snapshot (``todo_state``): a viewer attaching to a session
with a plan (the classic CLI's /resume or ``-c``) shows it before the next ``todo.updated``.

Real store, authority, local session and ``AuthorityConnection.resume`` (the helpers of
``test_resume_display_history``).
"""
import json

import pytest

from tests.gateway.test_resume_display_history import _local_session, _resume

TODOS = [{'id': '1', 'content': 'write the fix', 'status': 'completed'},
         {'id': '2', 'content': 'ship it', 'status': 'in_progress'}]


def _todo_turn(db, sid, call_id, todos, revision):
    call = {'id': call_id, 'type': 'function',
            'function': {'name': 'todo_list', 'arguments': json.dumps({'todos': todos})}}
    db.append_message(sid, 'assistant', '', tool_calls=[call])
    db.append_message(sid, 'tool', json.dumps({'todos': todos, 'revision': revision}), tool_name='todo_list',
                      tool_call_id=call_id)


@pytest.mark.asyncio
async def test_resume_carries_the_newest_todo_snapshot(tmp_path, monkeypatch):
    authority, actor, ref, physical = await _local_session(tmp_path, monkeypatch)
    db = authority.db
    assert (await _resume(authority, actor, ref))['todo_state'] is None  # no plan yet
    db.append_message(physical, 'user', 'plan it')
    _todo_turn(db, physical, 'call-1', TODOS[:1], 1)
    _todo_turn(db, physical, 'call-2', TODOS, 2)
    db.append_message(physical, 'assistant', 'planned')
    assert (await _resume(authority, actor, ref))['todo_state'] == {'todos': TODOS, 'revision': 2}
