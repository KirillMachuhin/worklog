from mongokit import RequireFieldError, ValidationError
import datetime
#import sys; sys.path.insert(0, '..')
from base import BaseModelsTestCase

class ModelsTestCase(BaseModelsTestCase):

    def test_create_user(self):
        user = self.db.User()
        assert user.guid
        assert user.add_date
        assert user.modify_date
        user.save()

        inst = self.db.users.User.one()
        assert inst.guid
        from utils import encrypt_password
        inst.password = encrypt_password('secret')
        inst.save()

        self.assertFalse(inst.check_password('Secret'))
        self.assertTrue(inst.check_password('secret'))

    def test_create_event(self):
        user = self.db.users.User()
        user.save()
        event = self.db.events.Event()
        event.user = user
        event.title = u"Test"
        event.all_day = True
        event.start = datetime.datetime.today()
        event.end = datetime.datetime.today()
        event.validate()
        event.save()

        self.assertEqual(self.db.events.Event.find().count(), 1)
        event = self.db.events.Event.one()

        assert self.db.events.Event.find({"user.$id":event.user._id}).count() == 1

    def test_create_event_with_blank_title(self):
        user = self.db.users.User()
        user.save()
        event = self.db.events.Event()
        event.user = user
        event.title = u" "
        event.all_day = True
        event.start = datetime.datetime.today() - datetime.timedelta(seconds=1)
        event.end = datetime.datetime.today()
        self.assertRaises(ValidationError, event.validate)
        self.assertRaises(ValidationError, event.save)

    def test_create_event_wrongly(self):
        user = self.db.users.User()
        user.save()
        event = self.db.events.Event()
        event.user = user
        event.title = u"Test"
        event.all_day = True
        event.start = datetime.datetime.today() + datetime.timedelta(seconds=1)
        event.end = datetime.datetime.today()
        self.assertRaises(ValidationError, event.validate)
        self.assertRaises(ValidationError, event.save)

        # but it can be equal
        event.start = datetime.datetime.today()
        event.end = datetime.datetime.today()
        event.validate()
        event.save()

    def test_user_settings(self):
        user = self.db.User()
        user.save()
        settings = self.db.UserSettings()

        self.assertRaises(RequireFieldError, settings.save)
        settings.user = user._id
        settings.save()

        self.assertFalse(settings.monday_first)
        self.assertFalse(settings.hide_weekend)

        model = self.db.UserSettings
        self.assertEqual(model.find({'user': user._id}).count(), 1)

    def test_create_share(self):
        user = self.db.User()
        user.save()
        share = self.db.Share()
        share.user = user._id
        share.save()

        self.assertEqual(share.tags, [])

        from apps.main.models import Share
        new_key = Share.generate_new_key(self.db.Share.collection, min_length=4)
        self.assertTrue(len(new_key) == 4)
        share.key = new_key
        share.save()

        self.assertTrue(self.db.Share.one(dict(key=new_key)))

    def test_create_feature_request(self):
        user = self.db.User()
        user.email = u'test@dot.com'
        user.save()

        feature_request = self.db.FeatureRequest()
        feature_request.author = user._id
        #self.assertRaises(RequireFieldError, feature_request.save)
        #feature_request.description = u"Bla bla"
        feature_request.save()

        frc = self.db.FeatureRequestComment()
        frc.feature_request = feature_request
        frc.save()
        self.assertEqual(frc.vote_weight, 1)

    def test_usersettings_bool_keys(self):
        from apps.main.models import UserSettings
        keys = UserSettings.get_bool_keys()
        self.assertTrue(isinstance(keys, list))
        self.assertTrue(keys) # at least one
        self.assertTrue(isinstance(keys[0], basestring))

    def test_usersettings_first_hour_validation(self):
        user = self.db.User()
        user.email = u'test@dot.com'
        user.save()

        user_settings = self.db.UserSettings()
        user_settings.user = user._id
        user_settings.save()
        self.assertTrue(user_settings.first_hour) # set to something

        user_settings.first_hour = 23
        user_settings.validate()
        user_settings.save() # should work

        user_settings.first_hour = -1
        self.assertRaises(ValidationError, user_settings.validate)
        self.assertRaises(ValidationError, user_settings.save)

        user_settings.first_hour = 24
        self.assertRaises(ValidationError, user_settings.validate)
        self.assertRaises(ValidationError, user_settings.save)
