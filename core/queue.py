from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit, Json, Set, count, raw_sql
from core.history import bind_db
from random import getrandbits
from uuid import getnode

"""If the bot has a large backlog of requests, we can queue a bunch of reverse tasks to distribute load"""

db = Database()

class QueueParticipants(db.Entity):
    uuid = PrimaryKey(str)
    tickets = Set('ReverseJobs')

class ReverseJobs(db.Entity):
    id = PrimaryKey(int, auto=True)
    context = Required(Json)
    origin_host = Required(int)
    origin_id = Required(str)
    assignee = Optional(QueueParticipants)

bind_db(db)

class Queue:
    def __init__(self):
        self.name = str(getnode())
        print("Queue name is", self.name)
        self.tag = None
        self.last_assigned = []

    def enter_queue(self):
        with db_session:
            # Check if UUID already in
            r = select(p for p in QueueParticipants if p.uuid == self.name)
            if len(r):  # We are already in here, lets use it
                self.tag = r.first()
                self.tag.active = True
            else:   # Add ourselves in
                self.tag = QueueParticipants(uuid=self.name)

    def exit_queue(self, uuid=None):
        if not uuid:
            uuid = self.name
        with db_session:
            tag = QueueParticipants[uuid]
            tag.delete()

    def add_job(self, context, gif):
        with db_session:
            job = ReverseJobs(context=context, origin_host=gif.host, origin_id=gif.id)
            assignee = select(p for p in QueueParticipants if p.uuid not in self.last_assigned)
            if not len(assignee):   # Used up all participants
                assignee = select(p for p in QueueParticipants)
                self.last_assigned = []
            if len(assignee):   # Skips if no participants available
                assignee = assignee.first()
                self.last_assigned.append(assignee.uuid)
                job.assignee = assignee

    def clean(self):
        with db_session:
            # If we have no jobs, reset the jobs autoincrement
            if not count(p for p in ReverseJobs):
                # r = db.execute("SELECT `AUTO_INCREMENT` FROM INFORMATION_SCHEMA.TABLES WHERE "
                #                "TABLE_SCHEMA = 'reddit_bots' AND TABLE_NAME = 'reversejobs';")
                # print(r)
                # r = db.execute("ALTER TABLE reversejobs AUTO_INCREMENT = 1")
                pass
            else:
                # Reassign jobs without participants
                if count(p for p in QueueParticipants):
                    jobs = select(j for j in ReverseJobs if j.assignee is None)
                    for job in jobs:
                        assignee = select(p for p in QueueParticipants if p.uuid not in self.last_assigned)
                        if not len(assignee):  # Used up all participants
                            assignee = select(p for p in QueueParticipants)
                            self.last_assigned = []
                        if len(assignee):  # Skips if no participants available
                            assignee = assignee.first()
                            self.last_assigned.append(assignee.uuid)
                            job.assignee = assignee

    def get_jobs(self):
        real_jobs = []
        with db_session:
            tag = QueueParticipants[self.name]
            jobs = list(select(j for j in ReverseJobs if j.assignee == tag))
            # Check for duplicates
            for i in jobs:
                d = select(j for j in ReverseJobs if j.origin_host == i.origin_host and j.origin_id == i.origin_id).limit(1)
                # If we aren't the first person in the list with this gif, ignore it
                if d[0].assignee == tag:
                    real_jobs.append(i)
        return real_jobs

    def remove_job(self, job: ReverseJobs):
        with db_session:
            job = ReverseJobs[job.id]
            tag = QueueParticipants[self.name]
            if job.assignee == tag:
                job.delete()
            else:
                Exception("Not this user's job")







