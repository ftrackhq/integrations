import ftrack_api


def with_session(func):
    def wrapper(*args, **kwargs):
        '''
        Creates an ftrack session and passes the session as an argument of the
        function
        '''
        result = None
        session = None
        try:
            # Create ftrack session
            session = ftrack_api.Session(auto_connect_event_hub=True)
            # Add session as argument
            kwargs['session'] = session
            # Call function
            result = func(*args, **kwargs)
        except Exception as error:
            raise Exception(
                "Error on creating a new session and executing method {}, "
                "error: {}".format(func, error)
            )
        finally:
            # Destroy session
            if session:
                session.close()
                del session
        return result

    return wrapper
