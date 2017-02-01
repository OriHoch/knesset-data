# -*- coding: utf-8 -*-
import logging
import os
import datetime
import csv
from base import (
    BaseKnessetDataServiceCollectionObject, BaseKnessetDataServiceFunctionObject,
    KnessetDataServiceSimpleField, KnessetDataServiceLambdaField
)
from knesset_data.protocols.committee import CommitteeMeetingProtocol
from knesset_data.datapackages.base import CsvResource, BaseDatapackage, BaseResource, FilesResource, CsvFilesResource
import json

logger = logging.getLogger('knesset_data.dataservice.committees')

IS_COMMITTEE_ACTIVE = 'committee_end_date eq null'
COMMITTEE_HAS_PORTAL_LINK = 'committee_portal_link ne null'


class Committee(BaseKnessetDataServiceCollectionObject):
    SERVICE_NAME = "committees"
    METHOD_NAME = "View_committee"
    DEFAULT_ORDER_BY_FIELD = "id"

    ORDERED_FIELDS = [
        ("id", KnessetDataServiceSimpleField('committee_id', "integer")),
        ("type_id", KnessetDataServiceSimpleField('committee_type_id', "integer")),
        ("parent_id", KnessetDataServiceSimpleField('committee_parent_id', "integer")),
        ("name", KnessetDataServiceSimpleField('committee_name', "string")),
        ("name_eng", KnessetDataServiceSimpleField('committee_name_eng', "string")),
        ("name_arb", KnessetDataServiceSimpleField('committee_name_arb', "string")),
        ("begin_date", KnessetDataServiceSimpleField('committee_begin_date', "datetime")),
        ("end_date", KnessetDataServiceSimpleField('committee_end_date', "datetime")),
        ("description", KnessetDataServiceSimpleField('committee_desc', "string")),
        ("description_eng", KnessetDataServiceSimpleField('committee_desc_eng', "string")),
        ("description_arb", KnessetDataServiceSimpleField('committee_desc_arb', "string")),
        ("note", KnessetDataServiceSimpleField('committee_note', "string")),
        ("note_eng", KnessetDataServiceSimpleField('committee_note_eng', "string")),
        ("portal_link", KnessetDataServiceSimpleField('committee_portal_link', "string")),
    ]

    @classmethod
    def get_all_active_committees(cls, has_portal_link=True, proxies=None):
        if has_portal_link:
            query = ' '.join((IS_COMMITTEE_ACTIVE, 'and', COMMITTEE_HAS_PORTAL_LINK))
        else:
            query = IS_COMMITTEE_ACTIVE
        params = {'$filter': query}
        return cls._get_all_pages(cls._get_url_base(), params, proxies=proxies)


class CommitteesResource(CsvResource):

    def __init__(self, name, parent_datapackage_path, meetings_resource=None):
        self._meetings_resource = meetings_resource
        json_table_schema = Committee.get_json_table_schema()
        super(CommitteesResource, self).__init__(name, parent_datapackage_path, json_table_schema)

    def _data_generator(self, **make_kwargs):
        proxies = make_kwargs.get('proxies')
        if make_kwargs.get('committee_ids'):
            self.logger.info('fetching commitee ids: {}'.format(make_kwargs["committee_ids"]))
            self.descriptor["description"] = "specific committee ids"
            committees = (Committee.get(committee_id, proxies=proxies)
                          for committee_id in make_kwargs["committee_ids"])
        elif make_kwargs.get('all_committees'):
            self.logger.info('fetching all committees')
            self.descriptor["description"] = "all committees"
            committees = Committee.get_all(proxies=proxies)
        elif make_kwargs.get('main_committees'):
            self.logger.info('fetching main committees')
            self.descriptor["description"] = "main committees"
            committees = Committee.get_all_active_committees(has_portal_link=True, proxies=proxies)
        else:
            self.logger.info('fetching active committees')
            self.descriptor["description"] = "active committees"
            committees = Committee.get_all_active_committees(has_portal_link=False, proxies=proxies)
        for committee in committees:
            if self._meetings_resource:
                self._meetings_resource.append_for_committee(committee, **make_kwargs)
            self.logger.debug('appending committee {}'.format(committee.id))
            yield committee.all_field_values()


class CommitteeMeeting(BaseKnessetDataServiceFunctionObject):
    SERVICE_NAME = "committees"
    METHOD_NAME = "CommitteeAgendaSearch"

    # the primary key of committee meetings
    id = KnessetDataServiceSimpleField('Committee_Agenda_id', 'integer')

    # id of the committee (linked to Committee object)
    committee_id = KnessetDataServiceSimpleField('Committee_Agenda_committee_id', 'integer')

    # date/time when the meeting started
    datetime = KnessetDataServiceSimpleField('committee_agenda_date', 'datetime')

    # title of the meeting
    title = KnessetDataServiceSimpleField('title', 'string')
    # seems like in some committee meetings, the title field is empty, in that case title can be taken from this field
    session_content = KnessetDataServiceSimpleField('committee_agenda_session_content', 'string')

    # url to download the protocol
    url = KnessetDataServiceSimpleField('url', 'string')

    # a CommitteeMeetingProtocol object which allows to get data from the protocol
    # because parsing the protocol requires heavy IO and processing - we provide it as a generator
    # see tests/test_meetings.py for usage example
    protocol = KnessetDataServiceLambdaField(lambda obj, entry:
                                             CommitteeMeetingProtocol.get_from_url(obj.url, proxies=obj._proxies)
                                             if obj.url else None)

    # this seems like a shorter name of the place where meeting took place
    location = KnessetDataServiceSimpleField('committee_location', 'string')

    # this looks like a longer field with the specific details of where the meeting took place
    place = KnessetDataServiceSimpleField('Committee_Agenda_place', 'string')

    # date/time when the meeting ended - this is not always available, in some meetings it's empty
    meeting_stop = KnessetDataServiceSimpleField('meeting_stop', 'string')

    ### following fields seem less interesting ###
    agenda_canceled = KnessetDataServiceSimpleField('Committee_Agenda_canceled')
    agenda_sub = KnessetDataServiceSimpleField('Committee_agenda_sub')
    agenda_associated = KnessetDataServiceSimpleField('Committee_agenda_associated')
    agenda_associated_id = KnessetDataServiceSimpleField('Committee_agenda_associated_id')
    agenda_special = KnessetDataServiceSimpleField('Committee_agenda_special')
    agenda_invited1 = KnessetDataServiceSimpleField('Committee_agenda_invited1')
    agenda_invite = KnessetDataServiceSimpleField('sd2committee_agenda_invite')
    note = KnessetDataServiceSimpleField('Committee_agenda_note')
    start_datetime = KnessetDataServiceSimpleField('StartDateTime')
    topid_id = KnessetDataServiceSimpleField('Topic_ID')
    creation_date = KnessetDataServiceSimpleField('Date_Creation')
    streaming_url = KnessetDataServiceSimpleField('streaming_url')
    meeting_start = KnessetDataServiceSimpleField('meeting_start')
    is_paused = KnessetDataServiceSimpleField('meeting_is_paused')
    date_order = KnessetDataServiceSimpleField('committee_date_order')
    date = KnessetDataServiceSimpleField('committee_date')
    day = KnessetDataServiceSimpleField('committee_day')
    month = KnessetDataServiceSimpleField('committee_month')
    material_id = KnessetDataServiceSimpleField('material_id')
    material_committee_id = KnessetDataServiceSimpleField('material_comittee_id')
    material_expiration_date = KnessetDataServiceSimpleField('material_expiration_date')
    material_hour = KnessetDataServiceSimpleField('committee_material_hour')
    old_url = KnessetDataServiceSimpleField('OldUrl')
    background_page_link = KnessetDataServiceSimpleField('CommitteeBackgroundPageLink')
    agenda_invited = KnessetDataServiceSimpleField('Committee_agenda_invited')

    @classmethod
    def get(cls, committee_id, from_date, to_date=None, proxies=None):
        """
        # example usage:
        >>> from datetime import datetime
        # get all meetings of committee 1 from Jan 01, 2016
        >>> CommitteeMeeting.get(1, datetime(2016, 1, 1))
        # get all meetings of committee 2 from Feb 01, 2015 to Feb 20, 2015
        >>> CommitteeMeeting.get(2, datetime(2015, 2, 1), datetime(2015, 2, 20))
        """
        params = {
            "CommitteeId": "'%s'" % committee_id,
            "FromDate": "'%sT00:00:00'" % from_date.strftime('%Y-%m-%d')
        }
        if to_date:
            params["ToDate"] = "'%sT00:00:00'" % to_date.strftime('%Y-%m-%d')
        return super(CommitteeMeeting, cls).get(params, proxies=proxies)


class CommitteeMeetingsResource(CsvResource):
    """
    Committee meetings csv resource - generates the csv with committee meetings for the last DAYS days (default 5 days)
    if __init__ gets a protocols resource it will pass every meeting over to that resource to save the corresponding protocol
    """

    def __init__(self, name, parent_datapackage_path, protocols_resource=None):
        self._protocols_resource = protocols_resource
        json_table_schema = CommitteeMeeting.get_json_table_schema()
        super(CommitteeMeetingsResource, self).__init__(name, parent_datapackage_path, json_table_schema)

    def append_for_committee(self, committee, **make_kwargs):
        if not self._skip_resource(**make_kwargs):
            proxies = make_kwargs.get('proxies', None)
            fromdate = datetime.datetime.now().date() - datetime.timedelta(days=make_kwargs.get('days', 5))
            self.logger.info('appending committee meetings since {} for committee {}'.format(fromdate, committee.id))
            meeting = empty = object()
            for meeting in CommitteeMeeting.get(committee.id, fromdate, proxies=proxies):
                if self._protocols_resource:
                    self._protocols_resource.append_for_meeting(committee, meeting, **make_kwargs)
                self.logger.debug('append committee meeting {}'.format(meeting.id))
                self._append(meeting.all_field_values())
            if meeting == empty:
                self.logger.debug('no meetings')


class CommitteeMeetingProtocolsResource(CsvFilesResource):

    def __init__(self, name, parent_datapackage_path, members_resource=None):
        self._members_resoure = members_resource
        super(CommitteeMeetingProtocolsResource, self).__init__(name, parent_datapackage_path,
                                                                {"fields": [{"type": "integer", "name": "committee_id"},
                                                                            {"type": "integer", "name": "meeting_id"},
                                                                            {"type": "string", "name": "text"},
                                                                            {"type": "string", "name": "parts"},
                                                                            {"type": "string", "name": "attending_members"}]})


    def append_for_meeting(self, committee, meeting, **make_kwargs):
        if not self._skip_resource(**make_kwargs) and meeting.protocol:
            self.logger.info('appending committee meeting protocols for committe {} meeting {}'.format(committee.id, meeting.id))
            if not os.path.exists(self._base_path):
                os.mkdir(self._base_path)
            # relative paths
            rel_committee_path = "committee_{}".format(committee.id)
            rel_meeting_path = os.path.join(rel_committee_path, "{}_{}".format(meeting.id, str(meeting.datetime).replace(' ', '_').replace(':','-')))
            rel_text_file_path = os.path.join(rel_meeting_path, "protocol.txt")
            rel_parts_file_path = os.path.join(rel_meeting_path, "protocol.csv")
            # absolute paths
            abs_committee_path = os.path.join(self._base_path, rel_committee_path)
            abs_meeting_path = os.path.join(self._base_path, rel_meeting_path)
            abs_text_file_path = os.path.join(self._base_path, rel_text_file_path)
            abs_parts_file_path = os.path.join(self._base_path, rel_parts_file_path)
            # create directories
            if not os.path.exists(abs_committee_path):
                os.mkdir(abs_committee_path)
            if not os.path.exists(abs_meeting_path):
                os.mkdir(abs_meeting_path)
            # parse the protocol and save
            with meeting.protocol as protocol:
                with open(abs_text_file_path, 'w') as f:
                    f.write(protocol.text.encode('utf8'))
                with open(abs_parts_file_path, 'wb') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow(["header", "body"])
                    for part in protocol.parts:
                        csv_writer.writerow([part.header.encode('utf8'), part.body.encode('utf8')])
                if self._members_resoure:
                    attending_member_names = protocol.find_attending_members([u"{} {}".format(member.first_name, member.name) for member
                                                                              in self._members_resoure.get_generated_members()])
                    attending_member_names = u", ".join(attending_member_names)
                else:
                    attending_member_names = ""
                self._append_file(abs_text_file_path, **make_kwargs)
                self._append_csv({"committee_id": committee.id,
                                  "meeting_id": meeting.id,
                                  "text": rel_text_file_path.lstrip("/"),
                                  "parts": rel_parts_file_path.lstrip("/"),
                                  "attending_members": attending_member_names}, **make_kwargs)
