from consumer import Consumer

# * Import whatever job should be called here
# from my_module import example_callback


def example_callback():
    ...


if __name__ == "__main__":
    # Instantiate our listener with the correct details
    consume = Consumer(
        # * Pass in the job to be executed here
        callback=example_callback,
        # ? Optional -> pass in the Queue credentials here instead of loading from env
        # username="my_username",
        # password="my_password",
    )

    # Start listening for messages
    # * Pass in the amount of workers (processes) you want to run, or leave empty for automatic configuration
    consume.consume(workers=4)

    # ! Code posted below this line will never be processed
