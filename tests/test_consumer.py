# from rabbie import Consumer, MicroConsumer
# from rabbie.consumer import Listener, ListenerDetails


# # Dependencies:
# # pip install pytest-mock
# import pytest


# class TestConsumer:
#     # Tests that a Consumer object can be created with valid parameters.
#     def test_create_consumer_with_valid_parameters(self):
#         # Happy path
#         consumer = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         assert consumer._host == "localhost"
#         assert consumer._port == "5672"
#         assert consumer._username == "guest"
#         assert consumer._password == "guest"

#     # Tests that the listen method can be called with valid parameters and a decorated function.
#     def test_listen_method_with_valid_parameters(self):
#         # Happy path
#         consumer = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )

#         @consumer.listen(queue="test_queue", workers=2)
#         def test_function():
#             pass

#         assert len(consumer.listeners) == 1
#         assert consumer.listeners[0].details.queue_name == "test_queue"
#         assert consumer.listeners[0].details.workers == 2

#     # Tests that the start method can be called with valid parameters.
#     def test_start_method_with_valid_parameters(self, mocker):
#         # Happy path
#         consumer = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         listener_mock = mocker.Mock()
#         listener_mock.start.return_value = None
#         consumer.listeners.append(listener_mock)
#         consumer.start(reload=False, halt=False)
#         listener_mock.start.assert_called_once()

#     # Tests that a valid Consumer or MicroConsumer object can be added to the listeners list.
#     def test_add_consumer_method_with_valid_parameters(self):
#         # Happy Path
#         consumer1 = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         consumer2 = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         microconsumer = MicroConsumer()

#         consumer1.add_consumer(consumer2)
#         assert len(consumer1.listeners) == len(consumer2.listeners)

#         consumer1.add_consumer(microconsumer)
#         assert len(consumer1.listeners) == len(consumer2.listeners) + len(
#             microconsumer._build_listeners(consumer1.connection_parameters)
#         )

#         # Edge Case
#         consumer1.add_consumer(None)
#         assert len(consumer1.listeners) == len(consumer2.listeners) + len(
#             microconsumer._build_listeners(consumer1.connection_parameters)
#         )

#     # Tests that the stop method stops all Listeners.
#     def test_stop_method(self):
#         # Important
#         consumer = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         listener1 = Listener(
#             connection_parameters=consumer.connection_parameters,
#             details=ListenerDetails(
#                 callback=lambda x: x,
#                 queue_name="test_queue",
#                 workers=1,
#                 decoder=None,
#                 restart=False,
#                 auto_ack=True,
#             ),
#         )
#         listener2 = Listener(
#             connection_parameters=consumer.connection_parameters,
#             details=ListenerDetails(
#                 callback=lambda x: x,
#                 queue_name="test_queue",
#                 workers=1,
#                 decoder=None,
#                 restart=False,
#                 auto_ack=True,
#             ),
#         )
#         consumer.listeners = [listener1, listener2]

#         for listener in consumer.listeners:
#             listener.start()

#         assert all([listener.is_listening() for listener in consumer.listeners])

#         consumer._stop_listeners()

#         assert not any([listener.is_listening() for listener in consumer.listeners])

#     # Tests that the _start_listeners method starts all Listeners.
#     def test_start_listeners_method(self, mocker):
#         # Create a mock Listener object
#         mock_listener = mocker.Mock()
#         mock_listener.start.return_value = None

#         # Add the mock Listener to the Consumer's listeners list
#         consumer = Consumer(
#             host="localhost", port="5672", username="guest", password="guest"
#         )
#         consumer.listeners.append(mock_listener)

#         # Call the _start_listeners method and assert that the mock Listener's start method was called
#         consumer._start_listeners()
#         mock_listener.start.assert_called_once()
