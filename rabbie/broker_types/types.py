from pika.adapters.blocking_connection import BlockingChannel as Channel
from pika.spec import Basic
from pika.spec import BasicProperties

Method = Basic.Deliver