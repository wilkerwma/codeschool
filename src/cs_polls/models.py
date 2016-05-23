from django.db import models
from codeschool.models import User
from codeschool.utils import lazy


class Poll(models.Model):
    """
    A poll in which users can choose one of many different choices.
    """

    name = models.CharField(max_length=200)
    short_description = models.TextField()
    long_description = models.TextField(blank=True)
    update_allowed = models.BooleanField(default=False)
    anonymous_vote = models.BooleanField(default=False)
    alternative_vote = models.BooleanField(default=False)
    voters = models.ManyToManyField(User, blank=True)

    @property
    def title(self):
        return self.name

    @lazy
    def vote_count(self):
        return self.votes.count()

    @lazy
    def condorcet_table(self):
        options = list(self.options.sort('index'))
        N = len(options)
        table = [[None for _ in range(N)] for _ in range(N)]
        for i in range(N):
            table[i][i] = 1
            for j in range(i + 1, N):
                result = options[i].condorcet_result(options[j])
                table[i][j] = table[j][i] = result
        return table
    
    @lazy
    def vote_list(self):
        """A list of all votes identified by option index."""

        if self.alternative_vote:
            return [[int(y) for y in x.option_list.split(',')]
                    for x in self.votes.all()]
        else:
            return [x.index for x in self.votes.all()]

    def __str__(self):
        return self.name

    def __getitem__(self, idx):
        """Return option from index."""

        try:
            return self.options.get(index=idx)
        except Option.DoesNotExist:
            raise KeyError(idx)

    def can_vote(self, user):
        """Return True if user can vote or update its vote."""

        if self.anonymous_vote and user in self.voters.all():
            return False
        if (not self.update_allowed) and user in self.voters.all():
            return False
        return True

    def list_options(self):
        """Return a sequence of options in the correct order for rendering."""

        return self.options.order_by('index')

    # Vote management
    def register_vote(self, user, choice):
        """Register a vote for user."""

        if not self.can_vote(user):
            raise PermissionError('cannot vote in this poll anymore')

        # Register vote using different methods
        def register_alternative(vote):
            choices = sorted(choice.items(), key=lambda x: x[1])
            votes = [x for (x, _) in choices]
            vote.option_list = ','.join(map(str, votes))

        def register_simple(vote):
            option = self.options.get(index=int(choice))
            vote.option = option

        def register(vote):
            if self.alternative_vote:
                register_alternative(vote)
            else:
                register_simple(vote)
            self.voters.add(user)
            vote.save()

        # Create vote instance and update
        try:
            register(self.votes.get(user=user))
        except Vote.DoesNotExist:
            if self.anonymous_vote:
                register(Vote(poll=self, user=None))
            else:
                register(Vote(poll=self, user=user))

    def clear_votes(self):
        """Clear all votes."""

        for vote in self.votes.all():
            vote.delete()

    # CRUD permissions
    def can_view(self, user):
        return True

    # Compute winners in the alternative vote rule
    def winner_condorcet(self):
        """Return winner using Condorcet criterion.

        The winner is the candidate who wins in a direct trial against all the
        other alternatives. If not Condorcet winner exists, return None."""

        options = list(self.options.all())
        option = options.pop()

        while options:
            other = options.pop()
            x, y = option.condorcet_result(other)
            if x < y:
                option = other
            elif x == y:
                # No condorcet winner when there is a draw
                if options:
                    option = options
                else:
                    return None
        return option

    # Other methods
    def second_round(self, nbest=2):
        """Return another poll object with the nbest most voted options in this
        poll."""

        raise NotImplemented


class Option(models.Model):
    """An option in a Poll."""

    class Meta:
        unique_together = [('index', 'poll')]

    index = models.IntegerField()
    poll = models.ForeignKey(Poll, related_name='options')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def fraction(self):
        """Return the fraction of the total number of votes for the given
        option."""

        n_total = self.poll.vote_count
        n = self.votes.count()
        if n_total == 0:
            return 0.0
        else:
            return n / n_total

    def percentage(self, format='%d'):
        """Return a percentage of total votes string formatted using the given
        format string."""

        return format % (100 * self.fraction())

    def alternative_wins(self):
        """Return the number of Condorset wins against other candidates."""

        wins = 0
        for other in self.others():
            x, y = self.condorcet_result(other)
            wins += x > y
        return wins

    def alternative_draws(self):
        """Return the number of Condorset draws against other candidates."""

        wins = 0
        for other in self.others():
            x, y = self.condorcet_result(other)
            wins += x == y
        return wins

    def alternative_losses(self):
        """Return the number of Condorset losses against other candidates."""

        wins = 0
        for other in self.others():
            x, y = self.condorcet_result(other)
            wins += x < y
        return wins

    def condorcet_result(self, other):
        """Return a tuple with the number of votes in a direct condorcet
        dispute with the other option."""

        A, B = self.index, other.index
        nA = nB = 0
        for vote in self.poll.vote_list:
            for i in vote:
                if i == A:
                    nA += 1
                    break
                if i == B:
                    nB += 1
                    break
        return (nA, nB)

    def others(self):
        """Iterate over all other option in the poll."""

        for option in self.poll.options.all():
            if option.pk != self.pk:
                yield option

    def __repr__(self):
        return  'Option(%r, %r)' % (self.index, self.name)


class Vote(models.Model):
    """A single vote to the Poll."""

    poll = models.ForeignKey(Poll, related_name='votes')
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    option = models.ForeignKey(
        Option,
        related_name='votes',
        blank=True,
        null=True
    )
    option_list = models.TextField()

    def __repr__(self):
        return 'Vote(%r, %r)' % (self.user.username, self.option.index)

