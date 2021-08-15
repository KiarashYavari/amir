from amir import subjects

# used in scripts/amir:
# def manageSubjects(self, sender):
#         dialog = subjects.Subjects()
#         self.connect("database-changed", dialog.dbChanged)
# which means the code word "database-changed" execute dialog.dbChanged
# and automatically passed sender and active path through it
subject_instance = subjects.Subjects()
subject_instance.dbChanged(None, None)  # need to set sender and active_dbpath
