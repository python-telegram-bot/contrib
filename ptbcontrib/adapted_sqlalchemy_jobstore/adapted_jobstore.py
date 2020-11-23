import pickle

import telegram
import apscheduler.job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram.ext import CallbackContext, Dispatcher


class AdaptedSQLAlchemyJobStore(SQLAlchemyJobStore):
    """
    Wraps apscheduler.SQLAlchemyJobStore to make telegram Job class storable.
    """
    
    def __init__(self, dispatcher: Dispatcher, *args, **kwargs):
        """
        :param dispatcher (:class:`telegram.ext.Dispatcher`): Dispatcher instance
            that will be passed to CallbackContext when recreating jobs.
        :param args: Arguments to be passed to the SQLAlchemyJobStore constructor.
        """

        super(AdaptedSQLAlchemyJobStore, self).__init__(*args, **kwargs)
        self.dispatcher = dispatcher

    def add_job(self, job: apscheduler.job) -> None:
        """
        Called from apscheduler's internals after adding a new job.

        Args:
            job (:obj:`apscheduler.job`): The job to be persisted.
        """
        
        job = self._prepare_job(job)
        super(AdaptedSQLAlchemyJobStore, self).add_job(job)

    def update_job(self, job: apscheduler.job) -> None:
        """
        Called from apscheduler's internals after updating a job.

        Args:
            job (:obj:`apscheduler.job`): The job to be updated.
        """
        job = self._prepare_job(job)
        super(AdaptedSQLAlchemyJobStore, self).update_job(job)

    def _prepare_job(self, job: apscheduler.job):
        """
        Erase all unpickable data from telegram.ext.Job

        Args:
            job (:obj:`apscheduler.job`): The job to be processed.
        """

        # depends on JobQueue._build_args (jobqueue.py:69)
        telegram_job = job.args[0].job if self.dispatcher.use_context else job.args[1]

        telegram_job_elements = {
            'context': telegram_job.context,
            'name': telegram_job.name
        }

        job.args = (telegram_job_elements,)
        return job

    def _reconstitute_job(self, job_state: str):
        """
        Called from apscheduler's internals when loading job.

        Args:
            job_state (:obj:`str`): String containing pickled job state.
        """
        job_state = pickle.loads(job_state)
        telegram_job_elements = job_state['args'][0]
        tg_job = telegram.ext.Job(callback=None,
                                  context=telegram_job_elements['context'],
                                  name=telegram_job_elements['name'])
        # depends on JobQueue._build_args (jobqueue.py:69)
        if self.dispatcher.use_context:
            ctx = CallbackContext.from_job(tg_job, self.dispatcher)
            args = (ctx,)
        else:
            args = (self.dispatcher.bot, tg_job)
        # picked from SQLAlchemyJobStore._reconstitute_job
        job_state['args'] = args
        job_state['jobstore'] = self
        job = apscheduler.job.Job.__new__(apscheduler.job.Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job